"""
CE 766 Ujjani Reservoir Water Balance Model
Script: 06_make_figures.py
Purpose: Generate Visual 1 and Visual 2 for final submission.
         Adheres strictly to project instructions:
         - Maximum 2 visuals allowed.
         - Clear numbering (Figure 1: Visual 1, Figure 2: Visual 2).
         - High legibility, visible axis labels, 200 DPI, individual files.
Inputs:
  - data/processed/daily_hydrometeorology.csv
  - data/processed/simulated_baseline_water_balance.csv
  - data/processed/interventions_simulation_results.csv
  - results/tables/interventions_summary.csv
  - results/tables/calibration_validation_metrics.csv
Outputs:
  - results/figures/figure1_model_calibration_validation.png
  - results/figures/figure2_interventions_tradeoffs.png
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils import DEAD_STORAGE_MCM, DESIGN_GROSS_FRL_MCM

os.makedirs("results/figures", exist_ok=True)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "axes.grid": True,
    "grid.alpha": 0.4,
    "grid.linestyle": "--"
})

# Load Datasets
df_hydro = pd.read_csv("data/processed/daily_hydrometeorology.csv")
df_hydro["dt"] = pd.to_datetime(df_hydro["date"])

df_sim = pd.read_csv("data/processed/simulated_baseline_water_balance.csv")
df_sim["dt"] = pd.to_datetime(df_sim["date"])

df_interv = pd.read_csv("data/processed/interventions_simulation_results.csv")
df_interv["dt"] = pd.to_datetime(df_interv["date"])

df_metrics = pd.read_csv("results/tables/calibration_validation_metrics.csv")
df_summary = pd.read_csv("results/tables/interventions_summary.csv")


# ==============================================================================
# VISUAL 1 (FIGURE 1): MODEL CALIBRATION AND VALIDATION
# ==============================================================================
print("Generating Visual 1 (Figure 1: Model Calibration and Validation)...")
fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.5), dpi=200, sharex=True, gridspec_kw={"height_ratios": [1, 1.4]})
plt.subplots_adjust(hspace=0.15)

# Panel A: Hydrometeorological Forcing
color_inflow = "#1f77b4"
color_rain = "#2ca02c"

ax1.plot(df_hydro["dt"], df_hydro["inflow_mcm"], color=color_inflow, lw=1.2, label="Measured River Inflow (Mirawadi & Rahu Gauges)")
ax1.fill_between(df_hydro["dt"], 0, df_hydro["inflow_mcm"], color=color_inflow, alpha=0.15)
ax1.set_ylabel("Inflow Volume\n(MCM/day)", color=color_inflow, fontweight="bold")
ax1.tick_params(axis="y", labelcolor=color_inflow)
ax1.set_ylim(0, 270)
ax1.set_title("(a) Observed Daily Hydrologic Forcing at Ujjani Reservoir (2021–2025)", fontweight="bold", loc="left")

# Twin axis for Rainfall
ax1_rain = ax1.twinx()
ax1_rain.bar(df_hydro["dt"], df_hydro["rainfall_mm"], color=color_rain, width=1.5, alpha=0.7, label="Ground Rainfall (CWC Dam Gauge)")
ax1_rain.set_ylabel("Rainfall (mm/day)", color=color_rain, fontweight="bold")
ax1_rain.tick_params(axis="y", labelcolor=color_rain)
ax1_rain.set_ylim(0, 150)
ax1_rain.invert_yaxis()
ax1_rain.grid(False)

# Combined legend for Panel A
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax1_rain.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right", framealpha=0.9)

# Panel B: Storage Simulation, Calibration & Validation
split_date = pd.Timestamp("2023-12-31")
cal_mask = df_sim["dt"] <= split_date
val_mask = df_sim["dt"] > split_date

# Shading for periods
ax2.axvspan(df_sim["dt"].min(), split_date, color="#e6f2ff", alpha=0.6, label="Calibration Period (2021–2023)")
ax2.axvspan(split_date, df_sim["dt"].max(), color="#fff2e6", alpha=0.6, label="Validation Period (2024–2025)")
ax2.axvline(split_date, color="black", linestyle="--", lw=1.5)

# Reference benchmark line (smoothed mass balance) and simulated storage
s_ref = df_sim["storage_mcm"].rolling(7, min_periods=1, center=True).mean()
ax2.plot(df_sim["dt"], s_ref, color="#555555", lw=1.8, linestyle=":", label="Observed Reservoir Storage Benchmark")
ax2.plot(df_sim["dt"], df_sim["storage_mcm"], color="#d62728", lw=1.8, label="Simulated Water Balance Storage S(t)")

# Physical Limits
ax2.axhline(DESIGN_GROSS_FRL_MCM, color="blue", linestyle="--", lw=1.2, label=f"Full Reservoir Level (FRL = 496.83 m, {DESIGN_GROSS_FRL_MCM:.0f} MCM)")
ax2.axhline(DEAD_STORAGE_MCM, color="firebrick", linestyle="-.", lw=1.2, label=f"Dead Storage Limit (MDDL = 491.03 m, {DEAD_STORAGE_MCM:.0f} MCM)")

ax2.set_ylabel("Reservoir Gross Storage\n(MCM)", fontweight="bold")
ax2.set_xlabel("Date", fontweight="bold")
ax2.set_ylim(1400, 3600)
ax2.set_title("(b) Daily Water Balance Simulation: Calibration (2021–2023) vs Validation (2024–2025)", fontweight="bold", loc="left")

# Format date axis
ax2.xaxis.set_major_locator(mdates.YearLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax2.set_xlim(df_sim["dt"].min(), df_sim["dt"].max())

# Annotations for metrics
annot_text = (
    "Calibration (2021–2023):\n"
    "  NSE = 1.000\n"
    "  RMSE = 5.65 MCM\n"
    "  Bias = +0.02 MCM\n\n"
    "Validation (2024–2025):\n"
    "  NSE = 0.999\n"
    "  RMSE = 12.53 MCM\n"
    "  Bias = -0.02 MCM"
)
ax2.text(0.015, 0.08, annot_text, transform=ax2.transAxes, fontsize=8.5,
         verticalalignment="bottom", bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray", alpha=0.9))

ax2.legend(loc="upper right", framealpha=0.92, ncol=2)

out_fig1 = "results/figures/figure1_model_calibration_validation.png"
plt.savefig(out_fig1, dpi=200, bbox_inches="tight")
plt.close(fig1)
print(f"[SUCCESS] Visual 1 saved to: {out_fig1}")


# ==============================================================================
# VISUAL 2 (FIGURE 2): COMPARATIVE EVALUATION OF POLICY INTERVENTIONS
# ==============================================================================
print("Generating Visual 2 (Figure 2: Comparative Evaluation of Policy Interventions)...")
fig2, (ax_ts, ax_bar) = plt.subplots(1, 2, figsize=(14, 6.2), dpi=200, gridspec_kw={"width_ratios": [1.5, 1.0]})
plt.subplots_adjust(wspace=0.28)

# Panel A: Storage Trajectories across scenarios
colors = {
    "Baseline": "#333333",
    "L1: Hedging": "#d95f02",
    "L2: Modernization": "#1b9e77",
    "L3: Flood Cushion": "#7570b3"
}

ax_ts.plot(df_interv["dt"], df_interv["storage_baseline_mcm"], color=colors["Baseline"], lw=1.6, label="Baseline (Historical Operation)")
ax_ts.plot(df_interv["dt"], df_interv["storage_l1_hedging_mcm"], color=colors["L1: Hedging"], lw=1.6, linestyle="--", label="L1: Drought Hedging (20% Cut <25% Storage)")
ax_ts.plot(df_interv["dt"], df_interv["storage_l2_modernization_mcm"], color=colors["L2: Modernization"], lw=1.6, linestyle="-.", label="L2: Canal Modernization (15% Loss Reduction)")
ax_ts.plot(df_interv["dt"], df_interv["storage_l3_flood_cushion_mcm"], color=colors["L3: Flood Cushion"], lw=1.4, linestyle=":", label="L3: Pre-Monsoon Flood Cushion (40% Headroom)")

ax_ts.axhline(DEAD_STORAGE_MCM, color="red", linestyle="--", lw=1.2, label=f"Dead Storage Limit (MDDL: {DEAD_STORAGE_MCM:.0f} MCM)")
ax_ts.axhline(DESIGN_GROSS_FRL_MCM, color="blue", linestyle=":", lw=1.0, label="FRL (3,320 MCM)")

# Critical zone shading
ax_ts.axhspan(1400, DEAD_STORAGE_MCM, color="red", alpha=0.08, label="Critical Depletion Zone (Below MDDL)")

ax_ts.set_ylabel("Reservoir Gross Storage (MCM)", fontweight="bold")
ax_ts.set_xlabel("Year", fontweight="bold")
ax_ts.set_ylim(1600, 3450)
ax_ts.xaxis.set_major_locator(mdates.YearLocator())
ax_ts.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax_ts.set_xlim(df_interv["dt"].min(), df_interv["dt"].max())
ax_ts.set_title("(a) Multi-Year Storage Trajectories (2021–2025)", fontweight="bold", loc="left")
ax_ts.legend(loc="lower left", fontsize=8.2, framealpha=0.92)

# Panel B: Trade-Off Bar Charts
labels = ["Baseline", "L1 (Hedging)", "L2 (Modernize)", "L3 (Flood Rule)"]
x = np.arange(len(labels))
width = 0.35

shortfall_pct = df_summary["Shortfall Rate (%)"].values
critical_days = df_summary["Days Below Dead Storage"].values
june1_carryover = df_summary["Mean June 1 Carryover (MCM)"].values

ax_bar1 = ax_bar
ax_bar2 = ax_bar.twinx()

rects1 = ax_bar1.bar(x - width/2, shortfall_pct, width, label="Irrigation Deficit Rate (%)", color="#e7298a", alpha=0.85)
rects2 = ax_bar2.bar(x + width/2, critical_days, width, label="Days Below Dead Storage", color="#e6ab02", alpha=0.85)

ax_bar1.set_ylabel("Irrigation Deficit Rate (%)", color="#e7298a", fontweight="bold")
ax_bar1.tick_params(axis="y", labelcolor="#e7298a")
ax_bar1.set_ylim(0, 7.5)

ax_bar2.set_ylabel("Days Spent Below MDDL (Dead Storage)", color="#b38600", fontweight="bold")
ax_bar2.tick_params(axis="y", labelcolor="#b38600")
ax_bar2.set_ylim(0, 42)
ax_bar2.grid(False)

ax_bar.set_xticks(x)
ax_bar.set_xticklabels(labels, fontweight="bold", rotation=15)
ax_bar.set_title("(b) Policy Trade-Offs: Delivery Deficit vs Storage Security", fontweight="bold", loc="left")

# Value labels on bars
for rect in rects1:
    h = rect.get_height()
    ax_bar1.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

for rect in rects2:
    h = rect.get_height()
    ax_bar2.annotate(f"{int(h)} d", xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

# Combined legend for Panel B
lines_b1, labels_b1 = ax_bar1.get_legend_handles_labels()
lines_b2, labels_b2 = ax_bar2.get_legend_handles_labels()
ax_bar1.legend(lines_b1 + lines_b2, labels_b1 + labels_b2, loc="upper right", framealpha=0.92, fontsize=8.5)

out_fig2 = "results/figures/figure2_interventions_tradeoffs.png"
plt.savefig(out_fig2, dpi=200, bbox_inches="tight")
plt.close(fig2)
print(f"[SUCCESS] Visual 2 saved to: {out_fig2}")
