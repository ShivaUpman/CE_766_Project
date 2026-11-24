"""
CE 766 Ujjani Reservoir Water Balance Model
Script: 01_clean_data.py
Purpose: Clean, parse, quality-check, and aggregate raw hydrometeorological and
         operational records into a contiguous daily time series (2021-01-01 to 2025-12-31).
Inputs:
  - data/raw/River Water Discharge_Mirawadi.xlsx (2021-01 to 2023-05)
  - data/raw/River Water Discharge_Rahu.xlsx (2023-06 to 2025-10)
  - data/raw/rainfall_manual_daily_cwc_mh_2021_2025.csv (CWC ground rain gauges)
  - data/raw/reservior_discharge_tel_hr_maharashtra_sw_mh_ujjani_dam_1_2021_2025.csv (spillway telemetry)
Outputs:
  - data/processed/daily_hydrometeorology.csv
"""

import os
import pandas as pd
import numpy as np

# 1. Date range definition
START_DATE = "2021-01-01"
END_DATE = "2025-12-31"
dates = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
df_daily = pd.DataFrame({"date": dates})
df_daily["date_str"] = df_daily["date"].dt.strftime("%Y-%m-%d")

# 2. Process Upstream River Inflow (Mirawadi + Rahu)
print("Processing upstream river inflow...")
inflow_records = []
for fpath, label in [
    ("data/raw/River Water Discharge_Mirawadi.xlsx", "Mirawadi"),
    ("data/raw/River Water Discharge_Rahu.xlsx", "Rahu")
]:
    if os.path.exists(fpath):
        df_sheet = pd.read_excel(fpath, sheet_name="River Water Discharge - River W", header=6)
        df_sheet["dt"] = pd.to_datetime(df_sheet["Data Time"], errors="coerce")
        df_sheet["flow_m3s"] = pd.to_numeric(df_sheet["Data Value"], errors="coerce")
        df_valid = df_sheet.dropna(subset=["dt", "flow_m3s"]).copy()
        df_valid["flow_m3s"] = df_valid["flow_m3s"].clip(lower=0.0)
        # Convert m3/s to daily volume: m3/s * 86400 / 1e6 = m3/s * 0.0864 MCM/day
        df_valid["inflow_mcm"] = df_valid["flow_m3s"] * 0.0864
        df_valid["date_str"] = df_valid["dt"].dt.strftime("%Y-%m-%d")
        inflow_records.append(df_valid[["date_str", "inflow_mcm", "flow_m3s"]])

if inflow_records:
    df_inflow_all = pd.concat(inflow_records).drop_duplicates(subset=["date_str"]).sort_values("date_str")
    df_daily = df_daily.merge(df_inflow_all[["date_str", "inflow_mcm", "flow_m3s"]], on="date_str", how="left")
else:
    df_daily["inflow_mcm"] = np.nan
    df_daily["flow_m3s"] = np.nan

# 3. Process CWC Ground Rainfall
print("Processing CWC rainfall records...")
rain_path = "data/raw/rainfall_manual_daily_cwc_mh_2021_2025.csv"
if os.path.exists(rain_path):
    df_rain_raw = pd.read_csv(rain_path)
    df_rain_raw["dt"] = pd.to_datetime(df_rain_raw["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
    df_rain_raw["rain_val"] = pd.to_numeric(df_rain_raw["Manual Daily Rainfall (mm)"], errors="coerce").fillna(0.0).clip(lower=0.0)
    df_rain_raw["date_str"] = df_rain_raw["dt"].dt.strftime("%Y-%m-%d")

    # Specific dam site rainfall
    df_ujjani_rain = df_rain_raw[df_rain_raw["Station"] == "Ujjani Reservoir"].groupby("date_str")["rain_val"].max().reset_index()
    df_ujjani_rain.rename(columns={"rain_val": "rain_dam_mm"}, inplace=True)

    # Basin catchment average (Pune and Solapur stations)
    basin_stations = ["Dhond", "Mirawadi", "Paragaon", "Phulgaon", "Rahu", "Takli", "Ujjani Reservoir"]
    df_basin_rain = df_rain_raw[df_rain_raw["Station"].isin(basin_stations)].groupby("date_str")["rain_val"].mean().reset_index()
    df_basin_rain.rename(columns={"rain_val": "rain_basin_mm"}, inplace=True)

    df_daily = df_daily.merge(df_ujjani_rain, on="date_str", how="left")
    df_daily = df_daily.merge(df_basin_rain, on="date_str", how="left")
    # Where on-site gauge is missing, fall back to basin average; fill rest with 0.0
    df_daily["rainfall_mm"] = df_daily["rain_dam_mm"].combine_first(df_daily["rain_basin_mm"]).fillna(0.0)
else:
    df_daily["rainfall_mm"] = 0.0

# 4. Process Dam Spillway Discharge Telemetry
print("Processing spillway gate telemetry...")
spill_path = "data/raw/reservior_discharge_tel_hr_maharashtra_sw_mh_ujjani_dam_1_2021_2025.csv"
if os.path.exists(spill_path):
    df_spill = pd.read_csv(spill_path)
    time_col = [c for c in df_spill.columns if "time" in c.lower()][0]
    gate_cols = [c for c in df_spill.columns if "discharge" in c.lower()]
    df_spill["total_cusec"] = df_spill[gate_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).sum(axis=1)
    df_spill["dt"] = pd.to_datetime(df_spill[time_col], format="%d-%m-%Y %H:%M", errors="coerce")
    df_spill = df_spill.dropna(subset=["dt"])
    # 1 cusec = 0.0283168 m3/s
    df_spill["total_m3s"] = df_spill["total_cusec"] * 0.0283168
    df_spill["date_str"] = df_spill["dt"].dt.strftime("%Y-%m-%d")
    # Daily mean spillway flow in m3/s converted to MCM/day
    df_spill_daily = df_spill.groupby("date_str")["total_m3s"].mean().reset_index()
    df_spill_daily["spillway_mcm"] = df_spill_daily["total_m3s"] * 0.0864
    df_daily = df_daily.merge(df_spill_daily[["date_str", "spillway_mcm"]], on="date_str", how="left")
else:
    df_daily["spillway_mcm"] = 0.0

# Fill non-telemetry spillway records with 0.0 (spill occurs only when reservoir is near FRL during high monsoon inflows)
df_daily["spillway_mcm"] = df_daily["spillway_mcm"].fillna(0.0)

# 5. Clean, Interpolate short gaps in inflow, and quality checks
df_daily["inflow_mcm"] = df_daily["inflow_mcm"].interpolate(method="linear", limit=3).fillna(0.0)
df_daily["flow_m3s"] = df_daily["flow_m3s"].interpolate(method="linear", limit=3).fillna(0.0)

# Save processed dataset
os.makedirs("data/processed", exist_ok=True)
out_csv = "data/processed/daily_hydrometeorology.csv"
cols_to_save = ["date", "inflow_mcm", "flow_m3s", "rainfall_mm", "spillway_mcm"]
df_daily[cols_to_save].to_csv(out_csv, index=False)
print(f"[SUCCESS] Cleaned daily dataset written to: {out_csv}")
print(f"Summary Statistics:\n{df_daily[cols_to_save].describe()}")
