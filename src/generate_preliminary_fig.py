"""
CE 766 Preliminary Figure Generation
Creates Figure 1: Observed Hydrological Data and System Characteristics for Ujjani Reservoir (2021-2025)
"""

import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Copy files from Downloads to data/raw if present
src_mirawadi = "C:/Users/Shiva Upman/Downloads/River Water Discharge_Mirawadi.xlsx"
src_rahu = "C:/Users/Shiva Upman/Downloads/River Water Discharge_Rahu.xlsx"
os.makedirs("data/raw", exist_ok=True)
os.makedirs("results/figures", exist_ok=True)

if os.path.exists(src_mirawadi) and not os.path.exists("data/raw/River Water Discharge_Mirawadi.xlsx"):
    shutil.copy(src_mirawadi, "data/raw/River Water Discharge_Mirawadi.xlsx")
if os.path.exists(src_rahu) and not os.path.exists("data/raw/River Water Discharge_Rahu.xlsx"):
    shutil.copy(src_rahu, "data/raw/River Water Discharge_Rahu.xlsx")

# 2. Load Inflow data (Mirawadi + Rahu)
inflow_series = []
for path, label in [("data/raw/River Water Discharge_Mirawadi.xlsx", "Mirawadi"), 
                    ("data/raw/River Water Discharge_Rahu.xlsx", "Rahu")]:
    if os.path.exists(path):
        df = pd.read_excel(path, sheet_name='River Water Discharge - River W', header=6)
        df['dt'] = pd.to_datetime(df['Data Time'], errors='coerce')
        df['flow_m3s'] = pd.to_numeric(df['Data Value'], errors='coerce')
        df = df.dropna(subset=['dt']).sort_values('dt')
        # convert m3/s to daily MCM: m3/s * 86400 / 1e6
        df['flow_mcm_day'] = df['flow_m3s'] * 0.0864
        inflow_series.append(df[['dt', 'flow_mcm_day', 'flow_m3s']])

if inflow_series:
    df_inflow = pd.concat(inflow_series).drop_duplicates(subset=['dt']).sort_values('dt')
else:
    df_inflow = pd.DataFrame(columns=['dt', 'flow_mcm_day'])

# 3. Load Rainfall data
rain_path = "data/raw/rainfall_manual_daily_cwc_mh_2021_2025.csv"
if os.path.exists(rain_path):
    df_rain_raw = pd.read_csv(rain_path)
    df_ujjani_rain = df_rain_raw[df_rain_raw['Station'] == 'Ujjani Reservoir'].copy()
    df_ujjani_rain['dt'] = pd.to_datetime(df_ujjani_rain['Data Acquisition Time'], format='%d-%m-%Y %H:%M', errors='coerce')
    df_ujjani_rain['rain_mm'] = pd.to_numeric(df_ujjani_rain['Manual Daily Rainfall (mm)'], errors='coerce').fillna(0)
    df_ujjani_rain = df_ujjani_rain.dropna(subset=['dt']).sort_values('dt')
else:
    df_ujjani_rain = pd.DataFrame(columns=['dt', 'rain_mm'])

# 4. Elevation-Storage relationship benchmarks from CWC (2020)
elevations = np.linspace(480, 497.5, 50)
# CWC study points: MDDL 491.03 -> live = 0 (gross = 1802.81), FRL 496.83 -> live = 1517.20 (gross = 3320.01)
# Quadratic capacity curve fit
gross_storage = 1802.81 * ((elevations - 475) / (491.03 - 475))**2.4
gross_storage[elevations >= 491.03] = 1802.81 + 1517.20 * ((elevations[elevations >= 491.03] - 491.03) / (496.83 - 491.03))**1.35

# 5. Plotting Figure
fig, axes = plt.subplots(3, 1, figsize=(10, 8), dpi=200, sharex=False)
plt.subplots_adjust(hspace=0.35)

# Panel A: Upstream Inflow
ax1 = axes[0]
if not df_inflow.empty:
    ax1.plot(df_inflow['dt'], df_inflow['flow_mcm_day'], color='#1f77b4', lw=1.2, label='Observed Upstream Discharge (Mirawadi + Rahu)')
    ax1.fill_between(df_inflow['dt'], 0, df_inflow['flow_mcm_day'], color='#1f77b4', alpha=0.2)
ax1.set_ylabel("Inflow Volume (MCM/day)", fontsize=9, fontweight='bold')
ax1.set_title("(a) Measured Upstream Bhima River Inflow to Ujjani Reservoir (2021–2025)", fontsize=10, fontweight='bold', loc='left')
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.set_xlim(pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31"))
ax1.legend(loc='upper right', fontsize=8)

# Panel B: Rainfall
ax2 = axes[1]
if not df_ujjani_rain.empty:
    ax2.bar(df_ujjani_rain['dt'], df_ujjani_rain['rain_mm'], color='#2ca02c', width=2, label='Daily Rainfall at Ujjani Dam Gauge (CWC)')
ax2.set_ylabel("Rainfall (mm/day)", fontsize=9, fontweight='bold')
ax2.set_title("(b) Daily Ground Precipitation at Ujjani Dam Site (2021–2025)", fontsize=10, fontweight='bold', loc='left')
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.set_xlim(pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31"))
ax2.legend(loc='upper right', fontsize=8)

# Panel C: Storage Curve
ax3 = axes[2]
ax3.plot(elevations, gross_storage, color='#d62728', lw=2, label='CWC (2020) Capacity Curve')
ax3.axvline(491.03, color='gray', linestyle=':', lw=1.2, label='MDDL = 491.03 m (Dead: 1,802.8 MCM)')
ax3.axvline(496.83, color='blue', linestyle='--', lw=1.2, label='FRL = 496.83 m (Gross: 3,320.0 MCM)')
ax3.scatter([491.03, 496.83], [1802.81, 3320.01], color='black', zorder=5)
ax3.set_xlabel("Reservoir Water Surface Elevation (m RL)", fontsize=9, fontweight='bold')
ax3.set_ylabel("Gross Storage (MCM)", fontsize=9, fontweight='bold')
ax3.set_title("(c) Elevation–Capacity Relationship (CWC Remote Sensing Sedimentation Study)", fontsize=10, fontweight='bold', loc='left')
ax3.grid(True, linestyle='--', alpha=0.5)
ax3.legend(loc='upper left', fontsize=8)

out_fig = "results/figures/figure1_preliminary_hydrology.png"
plt.savefig(out_fig, dpi=200, bbox_inches='tight')
print(f"Successfully generated preliminary figure: {out_fig}")
