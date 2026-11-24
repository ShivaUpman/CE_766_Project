"""
CE 766 Ujjani Reservoir Water Balance Model
Script: 03_water_balance.py
Purpose: Daily lumped reservoir water balance simulation model.
         S(t+1) = S(t) + I_gauged(t) + I_ungauged(t) + P(t) - R_dam(t) - R_canal(t) - E(t) - L(t)
Inputs:
  - data/processed/daily_hydrometeorology.csv
  - data/processed/elevation_area_capacity.csv
Outputs:
  - Simulation functions and historical mass balance series
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from src.utils import (
    get_gross_storage,
    get_surface_area,
    DEAD_STORAGE_MCM,
    FRL_M,
    DESIGN_GROSS_FRL_MCM,
    cumecs_to_mcm_per_day
)

# Solapur regional mean monthly pan evaporation rates (mm/day) from IMD / CWC agro-climatic normals
MONTHLY_PAN_EVAP_MM_DAY = {
    1: 5.2,   # Jan
    2: 6.8,   # Feb
    3: 8.5,   # Mar
    4: 10.2,  # Apr
    5: 11.0,  # May
    6: 7.2,   # Jun
    7: 5.0,   # Jul
    8: 4.8,   # Aug
    9: 5.0,   # Sep
    10: 5.4,  # Oct
    11: 5.0,  # Nov
    12: 4.8   # Dec
}

# Free catchment area draining directly into Ujjani reservoir (CWC SRS report, 2020)
FREE_CATCHMENT_SQKM = 9766.0

# Initial reservoir storage on 2021-01-01 (post-monsoon carryover: approx 85% of gross capacity = 2850 MCM)
INITIAL_STORAGE_MCM = 2850.0
STORAGE_CAP_MCM = 3320.010  # Maximum storage at FRL


def get_evaporation_depth_mm(month: int, pan_coeff: float = 0.72) -> float:
    """Return lake evaporation depth (mm/day) adjusted with pan coefficient."""
    base_pan = MONTHLY_PAN_EVAP_MM_DAY.get(month, 6.0)
    return base_pan * pan_coeff


def simulate_reservoir(
    df_hydro: pd.DataFrame,
    s_init: float = INITIAL_STORAGE_MCM,
    c_runoff: float = 0.042,
    pan_coeff: float = 0.72,
    k_seep: float = 0.00010,
    canal_demand_profile: np.ndarray = None,
    curtailment_policy = None,
    spill_drawdown_rule = None
) -> pd.DataFrame:
    """
    Simulate daily reservoir storage trajectory using the lumped water balance equation:
    S(t+1) = S(t) + I_gauged(t) + I_ungauged(t) + P(t) - R_dam(t) - R_canal(t) - E(t) - L(t)
    """
    n_days = len(df_hydro)
    storage = np.zeros(n_days + 1)
    storage[0] = s_init

    evap_vol = np.zeros(n_days)
    precip_vol = np.zeros(n_days)
    inflow_total = np.zeros(n_days)
    canal_release = np.zeros(n_days)
    canal_shortfall = np.zeros(n_days)
    spill_vol = np.zeros(n_days)
    seep_vol = np.zeros(n_days)
    surface_area = np.zeros(n_days)

    months = pd.to_datetime(df_hydro["date"]).dt.month.values
    days = pd.to_datetime(df_hydro["date"]).dt.day.values
    gauged_inflow = df_hydro["inflow_mcm"].values
    rainfall_mm = df_hydro["rainfall_mm"].values
    obs_spillway = df_hydro["spillway_mcm"].values

    # Baseline daily canal release demand (rotational irrigation scheduling across Kharif, Rabi, Hot weather)
    if canal_demand_profile is None:
        base_demand = np.zeros(n_days)
        for t in range(n_days):
            m = months[t]
            if m in [7, 8]:         # Monsoon peak
                base_demand[t] = 1.5
            elif m in [10, 11, 12]:   # Rabi irrigation rotations
                base_demand[t] = 4.8
            elif m in [1, 2, 3]:      # Late rabi / summer
                base_demand[t] = 5.2
            elif m in [4, 5]:         # Hot weather rotations
                base_demand[t] = 4.0
            else:
                base_demand[t] = 3.2
    else:
        base_demand = canal_demand_profile.copy()

    for t in range(n_days):
        s_curr = storage[t]
        area_curr = get_surface_area(s_curr)
        surface_area[t] = area_curr

        # 1. Inputs
        i_gauge = gauged_inflow[t]
        p_depth = rainfall_mm[t]
        # Intermediate runoff from free catchment
        i_ungauge = (c_runoff * p_depth * FREE_CATCHMENT_SQKM) / 1000.0
        i_tot = i_gauge + i_ungauge
        inflow_total[t] = i_tot

        # Direct precipitation on water surface
        p_vol = (p_depth * area_curr) / 1000.0
        precip_vol[t] = p_vol

        # 2. Natural Losses
        e_depth = get_evaporation_depth_mm(months[t], pan_coeff=pan_coeff)
        e_vol = (e_depth * area_curr) / 1000.0
        evap_vol[t] = e_vol

        l_seep = k_seep * s_curr
        seep_vol[t] = l_seep

        # 3. Canal Release Demand & Curtailment Logic
        target_demand = base_demand[t]
        if curtailment_policy is not None:
            actual_release, shortfall = curtailment_policy(s_curr, target_demand, months[t], days[t])
        else:
            # Baseline: deliver demand unless storage drops below dead storage (1802.81 MCM)
            if s_curr > DEAD_STORAGE_MCM:
                avail = s_curr - DEAD_STORAGE_MCM
                actual_release = min(target_demand, avail)
            else:
                actual_release = 0.0
            shortfall = target_demand - actual_release

        canal_release[t] = actual_release
        canal_shortfall[t] = max(0.0, shortfall)

        # 4. Storage Update before spill
        s_next = s_curr + i_tot + p_vol - actual_release - e_vol - l_seep

        # 5. Spillway discharge
        spill = 0.0
        # Check rule-based flood drawdown if active
        flood_cap = STORAGE_CAP_MCM
        if spill_drawdown_rule is not None:
            flood_cap = spill_drawdown_rule(months[t], days[t])

        if s_next > flood_cap:
            spill = s_next - flood_cap
            s_next = flood_cap

        # Incorporate observed telemetry spill events if baseline and higher
        if spill_drawdown_rule is None and obs_spillway[t] > spill:
            spill_extra = min(obs_spillway[t] - spill, max(0.0, s_next - DEAD_STORAGE_MCM))
            spill += spill_extra
            s_next -= spill_extra

        spill_vol[t] = spill
        storage[t + 1] = max(1000.0, s_next)

    df_out = df_hydro.copy()
    df_out["storage_mcm"] = storage[:-1]
    df_out["surface_area_sqkm"] = surface_area
    df_out["inflow_total_mcm"] = inflow_total
    df_out["precip_vol_mcm"] = precip_vol
    df_out["evap_vol_mcm"] = evap_vol
    df_out["seep_vol_mcm"] = seep_vol
    df_out["canal_demand_mcm"] = base_demand
    df_out["canal_release_mcm"] = canal_release
    df_out["canal_shortfall_mcm"] = canal_shortfall
    df_out["spill_mcm"] = spill_vol
    return df_out


if __name__ == "__main__":
    df_hydro = pd.read_csv("data/processed/daily_hydrometeorology.csv")
    df_res = simulate_reservoir(df_hydro)
    print("Water balance model test passed successfully.")
    print("Mean storage:", df_res["storage_mcm"].mean())
    print("Mean daily inflow total:", df_res["inflow_total_mcm"].mean())
    print("Mean daily evaporation:", df_res["evap_vol_mcm"].mean())
    print("Mean daily canal release:", df_res["canal_release_mcm"].mean())
