"""
CE 766 Ujjani Reservoir Water Balance Model
Script: 07_sensitivity_analysis.py
Purpose: Perform One-At-A-Time (OAT) parameter sensitivity analysis (+/- 20% variation)
         on key hydrologic parameters: pan evaporation coefficient, runoff coefficient, and seepage.
         Strictly adheres to AGENTS.md Hard Rule 1 (simple, explainable science; no Sobol/Monte Carlo).
Inputs:
  - data/processed/daily_hydrometeorology.csv
Outputs:
  - results/tables/sensitivity_analysis.csv
"""

import os
import sys
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from src.utils import DEAD_STORAGE_MCM

wb_mod = importlib.import_module("src.03_water_balance")
simulate_reservoir = wb_mod.simulate_reservoir

# Baseline calibrated parameters
BASE_RUNOFF = 0.045
BASE_PAN = 0.74
BASE_SEEP = 0.00010


def run_sensitivity():
    df_hydro = pd.read_csv("data/processed/daily_hydrometeorology.csv")
    
    # Baseline run
    df_base = simulate_reservoir(df_hydro, c_runoff=BASE_RUNOFF, pan_coeff=BASE_PAN, k_seep=BASE_SEEP)
    base_mean_s = df_base["storage_mcm"].mean()
    base_min_s = df_base["storage_mcm"].min()
    base_short = df_base["canal_shortfall_mcm"].sum()
    base_crit_days = (df_base["storage_mcm"] <= DEAD_STORAGE_MCM).sum()

    experiments = [
        ("Baseline (Calibrated)", BASE_RUNOFF, BASE_PAN, BASE_SEEP),
        ("Runoff Coeff +20%", BASE_RUNOFF * 1.20, BASE_PAN, BASE_SEEP),
        ("Runoff Coeff -20%", BASE_RUNOFF * 0.80, BASE_PAN, BASE_SEEP),
        ("Pan Evap Coeff +20%", BASE_RUNOFF, BASE_PAN * 1.20, BASE_SEEP),
        ("Pan Evap Coeff -20%", BASE_RUNOFF, BASE_PAN * 0.80, BASE_SEEP),
        ("Seepage Coeff +20%", BASE_RUNOFF, BASE_PAN, BASE_SEEP * 1.20),
        ("Seepage Coeff -20%", BASE_RUNOFF, BASE_PAN, BASE_SEEP * 0.80),
    ]

    results = []
    for label, cr, kp, ks in experiments:
        df_sim = simulate_reservoir(df_hydro, c_runoff=cr, pan_coeff=kp, k_seep=ks)
        mean_s = df_sim["storage_mcm"].mean()
        min_s = df_sim["storage_mcm"].min()
        shortfall = df_sim["canal_shortfall_mcm"].sum()
        crit_days = (df_sim["storage_mcm"] <= DEAD_STORAGE_MCM).sum()

        pct_change_mean_s = ((mean_s - base_mean_s) / base_mean_s) * 100.0

        results.append({
            "Experiment": label,
            "c_runoff": round(cr, 4),
            "pan_coeff": round(kp, 3),
            "k_seep": round(ks, 6),
            "Mean Storage (MCM)": round(mean_s, 1),
            "Min Storage (MCM)": round(min_s, 1),
            "Irrigation Deficit (MCM)": round(shortfall, 1),
            "Days Below Dead Storage": int(crit_days),
            "Mean Storage Change (%)": round(pct_change_mean_s, 2)
        })

    df_out = pd.DataFrame(results)
    os.makedirs("results/tables", exist_ok=True)
    out_path = "results/tables/sensitivity_analysis.csv"
    df_out.to_csv(out_path, index=False)
    print(f"[SUCCESS] Sensitivity analysis saved to: {out_path}")
    print("\nSensitivity Analysis Table:")
    print(df_out.to_string(index=False))


if __name__ == "__main__":
    run_sensitivity()
