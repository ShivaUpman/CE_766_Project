"""
CE 766 Ujjani Reservoir Water Balance Model
Script: 05_interventions.py
Purpose: Formulate, simulate, and compare 3-4 realistic management interventions
         grounded in MWRRA and Maharashtra Water Resources policy against historical baseline.
Inputs:
  - data/processed/daily_hydrometeorology.csv
Outputs:
  - data/processed/interventions_simulation_results.csv
  - results/tables/interventions_summary.csv
"""

import os
import sys
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from src.utils import DEAD_STORAGE_MCM, FRL_M, DESIGN_GROSS_FRL_MCM, LIVE_CAPACITY_MCM

wb_mod = importlib.import_module("src.03_water_balance")
simulate_reservoir = wb_mod.simulate_reservoir
INITIAL_STORAGE_MCM = wb_mod.INITIAL_STORAGE_MCM
STORAGE_CAP_MCM = wb_mod.STORAGE_CAP_MCM

# Policy Thresholds
# Live capacity = 1517.20 MCM. Dead storage = 1802.81 MCM.
# 25% live storage threshold = 1802.81 + 0.25 * 1517.20 = 2182.11 MCM
HEDGING_STORAGE_THRESHOLD_MCM = DEAD_STORAGE_MCM + 0.25 * LIVE_CAPACITY_MCM
# 60% live storage cap for flood cushion = 1802.81 + 0.60 * 1517.20 = 2713.13 MCM
FLOOD_CUSHION_CAP_MCM = DEAD_STORAGE_MCM + 0.60 * LIVE_CAPACITY_MCM


# --- Intervention Rules ---
def rule_l1_hedging(s_curr, target_demand, month, day):
    """
    Intervention 1 (L1 - Storage-Triggered Drought Hedging):
    Curtail non-priority canal releases by 20% when gross storage drops below 2,182.11 MCM (25% live storage),
    protecting critical drinking water supply and hot-weather carryover storage.
    """
    if s_curr <= DEAD_STORAGE_MCM:
        return 0.0, target_demand
    avail = s_curr - DEAD_STORAGE_MCM
    if s_curr < HEDGING_STORAGE_THRESHOLD_MCM:
        # 20% curtailment to preserve storage
        curtailed_target = 0.80 * target_demand
        actual_release = min(curtailed_target, avail)
    else:
        actual_release = min(target_demand, avail)
    shortfall = target_demand - actual_release
    return actual_release, shortfall


def rule_l3_flood_cushion(month, day):
    """
    Intervention 3 (L3 - Dynamic Pre-Monsoon Drawdown Rule):
    Cap storage at 2,713.13 MCM (60% live capacity) between 1 June and 15 July to provide
    a 606.88 MCM flood cushion against upstream cloudbursts and Pune dam spills.
    After 15 July, allow normal filling up to FRL (3,320.01 MCM).
    """
    if month == 6 or (month == 7 and day <= 15):
        return FLOOD_CUSHION_CAP_MCM
    return STORAGE_CAP_MCM


def run_interventions():
    df_hydro = pd.read_csv("data/processed/daily_hydrometeorology.csv")
    df_hydro["dt"] = pd.to_datetime(df_hydro["date"])
    n_days = len(df_hydro)
    months = df_hydro["dt"].dt.month.values

    # Base canal demand profile
    base_demand = np.zeros(n_days)
    for t in range(n_days):
        m = months[t]
        if m in [7, 8]:
            base_demand[t] = 1.5
        elif m in [10, 11, 12]:
            base_demand[t] = 4.8
        elif m in [1, 2, 3]:
            base_demand[t] = 5.2
        elif m in [4, 5]:
            base_demand[t] = 4.0
        else:
            base_demand[t] = 3.2

    # --- Scenario 1: Baseline (Historical Operations) ---
    print("Simulating Scenario 0: Baseline...")
    df_base = simulate_reservoir(df_hydro, canal_demand_profile=base_demand)

    # --- Scenario 2: Intervention L1 (Storage-Triggered Drought Hedging) ---
    print("Simulating Scenario 1: Intervention L1 (Drought Hedging Rule)...")
    df_l1 = simulate_reservoir(df_hydro, canal_demand_profile=base_demand, curtailment_policy=rule_l1_hedging)

    # --- Scenario 3: Intervention L2 (Canal Modernization & Loss Reduction) ---
    print("Simulating Scenario 2: Intervention L2 (Canal Modernization)...")
    # 15% reduction in gross diversion demand needed to meet the same agricultural water duty
    demand_l2 = base_demand * 0.85
    df_l2 = simulate_reservoir(df_hydro, canal_demand_profile=demand_l2)

    # --- Scenario 4: Intervention L3 (Dynamic Pre-Monsoon Flood Cushion) ---
    print("Simulating Scenario 3: Intervention L3 (Flood Cushion Rule)...")
    df_l3 = simulate_reservoir(df_hydro, canal_demand_profile=base_demand, spill_drawdown_rule=rule_l3_flood_cushion)

    # Combine simulations into master dataset
    df_combined = pd.DataFrame({
        "date": df_hydro["date"],
        "inflow_total_mcm": df_base["inflow_total_mcm"],
        "storage_baseline_mcm": df_base["storage_mcm"],
        "storage_l1_hedging_mcm": df_l1["storage_mcm"],
        "storage_l2_modernization_mcm": df_l2["storage_mcm"],
        "storage_l3_flood_cushion_mcm": df_l3["storage_mcm"],
        "canal_release_base_mcm": df_base["canal_release_mcm"],
        "canal_release_l1_mcm": df_l1["canal_release_mcm"],
        "canal_release_l2_mcm": df_l2["canal_release_mcm"],
        "canal_release_l3_mcm": df_l3["canal_release_mcm"],
        "shortfall_base_mcm": df_base["canal_shortfall_mcm"],
        "shortfall_l1_mcm": df_l1["canal_shortfall_mcm"],
        "shortfall_l2_mcm": df_l2["canal_shortfall_mcm"],
        "shortfall_l3_mcm": df_l3["canal_shortfall_mcm"],
        "spill_base_mcm": df_base["spill_mcm"],
        "spill_l1_mcm": df_l1["spill_mcm"],
        "spill_l2_mcm": df_l2["spill_mcm"],
        "spill_l3_mcm": df_l3["spill_mcm"],
    })

    os.makedirs("data/processed", exist_ok=True)
    out_all_csv = "data/processed/interventions_simulation_results.csv"
    df_combined.to_csv(out_all_csv, index=False)
    print(f"[SUCCESS] Combined simulation time series saved to: {out_all_csv}")

    # Compute Performance Measures (M)
    total_base_demand = base_demand.sum()
    total_l2_demand = demand_l2.sum()

    # June 1st carryover extraction
    df_hydro["is_june_1"] = (df_hydro["dt"].dt.month == 6) & (df_hydro["dt"].dt.day == 1)

    scenarios = [
        ("Baseline (Historical)", df_base, total_base_demand, "shortfall_base_mcm", "storage_baseline_mcm", "spill_base_mcm"),
        ("L1: Drought Hedging (20% Cut <25% Storage)", df_l1, total_base_demand, "shortfall_l1_mcm", "storage_l1_hedging_mcm", "spill_l1_mcm"),
        ("L2: Canal Modernization (15% Loss Reduction)", df_l2, total_l2_demand, "shortfall_l2_mcm", "storage_l2_modernization_mcm", "spill_l2_mcm"),
        ("L3: Pre-Monsoon Flood Cushion (40% Headroom)", df_l3, total_base_demand, "shortfall_l3_mcm", "storage_l3_flood_cushion_mcm", "spill_l3_mcm")
    ]

    summary_rows = []
    for name, df_scen, dem, s_col, st_col, sp_col in scenarios:
        tot_deliv = df_scen["canal_release_mcm"].sum()
        tot_short = df_scen["canal_shortfall_mcm"].sum()
        pct_short = (tot_short / dem) * 100.0
        min_stor = df_scen["storage_mcm"].min()
        mean_stor = df_scen["storage_mcm"].mean()
        days_critical = (df_scen["storage_mcm"] <= DEAD_STORAGE_MCM).sum()
        june1_stor = df_combined.loc[df_hydro["is_june_1"], st_col].mean()
        tot_spill = df_scen["spill_mcm"].sum()
        spill_days = (df_scen["spill_mcm"] > 0.0).sum()

        summary_rows.append({
            "Intervention Scenario": name,
            "Total Demand (MCM)": round(dem, 1),
            "Total Delivered (MCM)": round(tot_deliv, 1),
            "Irrigation Deficit (MCM)": round(tot_short, 1),
            "Shortfall Rate (%)": round(pct_short, 1),
            "Minimum Storage (MCM)": round(min_stor, 1),
            "Mean Storage (MCM)": round(mean_stor, 1),
            "Mean June 1 Carryover (MCM)": round(june1_stor, 1),
            "Days Below Dead Storage": int(days_critical),
            "Total Flood Spill (MCM)": round(tot_spill, 1),
            "Spill Days": int(spill_days)
        })

    summary_df = pd.DataFrame(summary_rows)
    os.makedirs("results/tables", exist_ok=True)
    out_summary_table = "results/tables/interventions_summary.csv"
    summary_df.to_csv(out_summary_table, index=False)
    print(f"\n[SUCCESS] Intervention comparison table saved to: {out_summary_table}")
    print("\nSummary Table:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    run_interventions()
