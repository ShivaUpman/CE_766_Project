"""
CE 766 Ujjani Reservoir Water Balance Model
Script: 02_storage_curve.py
Purpose: Model the Elevation-Area-Capacity relationship of Ujjani Reservoir
         using digitized data from the CWC (2020) Satellite Remote Sensing Sedimentation Study.
Inputs:
  - CWC (2020) SRS Sedimentation Study benchmark tables
Outputs:
  - data/processed/elevation_area_capacity.csv
"""

import os
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# CWC SRS (2020) Sedimentation Assessment Report Table 6 & Table 8 Benchmarks
# Dead storage capacity at MDDL (491.03 m) = 1,802.81 MCM
# Designed FRL (496.83 m) gross capacity = 3,320.01 MCM, live capacity = 1,517.20 MCM
# Post-sedimentation live capacity (SRS 2017-18) = 1,347.074 MCM (170.13 MCM loss)
DEAD_STORAGE_MCM = 1802.810
MDDL_M = 491.030
FRL_M = 496.830
DESIGN_GROSS_FRL_MCM = 3320.010

cwc_data = [
    # Elevation (m), Water Spread Area (sq km), Cumulative Live Storage (MCM), Gross Storage (MCM)
    (485.000, 105.000, 0.000, 1000.000),      # Bottom extrapolation
    (488.000, 142.000, 0.000, 1400.000),
    (491.030, 182.300, 0.000, 1802.810),      # MDDL
    (492.000, 199.564, 185.141, 1987.951),
    (493.000, 216.991, 393.357, 2196.167),
    (494.000, 234.042, 618.820, 2421.630),
    (495.000, 250.718, 861.152, 2663.962),
    (496.000, 267.017, 1119.977, 2922.787),
    (496.830, 280.260, 1347.074, 3149.884),   # FRL (SRS capacity)
    (497.580, 295.500, 1558.000, 3360.810),   # MWL
]

df_curve = pd.DataFrame(cwc_data, columns=["elevation_m", "area_sqkm", "live_storage_mcm", "gross_storage_mcm"])

# Save benchmark table
os.makedirs("data/processed", exist_ok=True)
out_csv = "data/processed/elevation_area_capacity.csv"
df_curve.to_csv(out_csv, index=False)
print(f"[SUCCESS] Elevation-area-capacity table saved to: {out_csv}")

# Interpolation functions
f_elev_to_storage = interp1d(df_curve["elevation_m"], df_curve["gross_storage_mcm"], kind="cubic", fill_value="extrapolate")
f_storage_to_elev = interp1d(df_curve["gross_storage_mcm"], df_curve["elevation_m"], kind="cubic", fill_value="extrapolate")
f_storage_to_area = interp1d(df_curve["gross_storage_mcm"], df_curve["area_sqkm"], kind="linear", fill_value="extrapolate")


def get_gross_storage(elevation_m: float) -> float:
    return float(f_elev_to_storage(elevation_m))


def get_elevation(gross_storage_mcm: float) -> float:
    return float(f_storage_to_elev(gross_storage_mcm))


def get_surface_area(gross_storage_mcm: float) -> float:
    return float(np.clip(f_storage_to_area(gross_storage_mcm), 100.0, 320.0))


if __name__ == "__main__":
    print("\n--- Validation against CWC Benchmarks ---")
    test_levels = [491.03, 494.00, 496.83]
    for h in test_levels:
        s = get_gross_storage(h)
        a = get_surface_area(s)
        h_rec = get_elevation(s)
        print(f"Elevation: {h:.2f} m -> Gross Storage: {s:.2f} MCM, Area: {a:.2f} sq km, Reconstructed Elevation: {h_rec:.2f} m")

    print("\nCWC MDDL Dead Storage Check:")
    print(f"CWC Value: {DEAD_STORAGE_MCM} MCM | Model Value: {get_gross_storage(MDDL_M):.2f} MCM")
    print("\nCWC FRL Storage Check:")
    print(f"CWC SRS Value: 3149.88 MCM | Model Value: {get_gross_storage(FRL_M):.2f} MCM")
