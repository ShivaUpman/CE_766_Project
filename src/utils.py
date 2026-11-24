"""
CE 766 Ujjani Reservoir Water Balance Model
Utility module: Named helper functions for unit conversions, elevation-storage curves, and performance metrics.

Units convention:
- Volume: Million Cubic Metres (MCM)
- Water Level: Metres (m)
- Flow Rate: Cubic metres per second (m³/s)
- Rain / Evaporation Depth: Millimetres (mm)
"""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# CWC SRS (2020) Sedimentation Assessment Report Table 6 & Table 8 Benchmarks
DEAD_STORAGE_MCM = 1802.810
MDDL_M = 491.030
FRL_M = 496.830
DESIGN_GROSS_FRL_MCM = 3320.010
LIVE_CAPACITY_MCM = 1517.200

# Benchmark curve coordinates
_CWC_DATA = [
    (485.000, 105.000, 0.000, 1000.000),
    (488.000, 142.000, 0.000, 1400.000),
    (491.030, 182.300, 0.000, 1802.810),
    (492.000, 199.564, 185.141, 1987.951),
    (493.000, 216.991, 393.357, 2196.167),
    (494.000, 234.042, 618.820, 2421.630),
    (495.000, 250.718, 861.152, 2663.962),
    (496.000, 267.017, 1119.977, 2922.787),
    (496.830, 280.260, 1347.074, 3149.884),
    (497.580, 295.500, 1558.000, 3360.810),
]
_df_curve = pd.DataFrame(_CWC_DATA, columns=["elevation_m", "area_sqkm", "live_storage_mcm", "gross_storage_mcm"])

_f_elev_to_storage = interp1d(_df_curve["elevation_m"], _df_curve["gross_storage_mcm"], kind="cubic", fill_value="extrapolate")
_f_storage_to_elev = interp1d(_df_curve["gross_storage_mcm"], _df_curve["elevation_m"], kind="cubic", fill_value="extrapolate")
_f_storage_to_area = interp1d(_df_curve["gross_storage_mcm"], _df_curve["area_sqkm"], kind="linear", fill_value="extrapolate")


def get_gross_storage(elevation_m: float) -> float:
    """Return gross storage (MCM) given water surface elevation (m)."""
    return float(_f_elev_to_storage(elevation_m))


def get_elevation(gross_storage_mcm: float) -> float:
    """Return water surface elevation (m) given gross storage (MCM)."""
    return float(_f_storage_to_elev(gross_storage_mcm))


def get_surface_area(gross_storage_mcm: float) -> float:
    """Return reservoir water spread area (sq km) given gross storage (MCM)."""
    return float(np.clip(_f_storage_to_area(gross_storage_mcm), 100.0, 320.0))


def cumecs_to_mcm_per_day(discharge_cumecs: float) -> float:
    """
    Convert discharge in m³/s (cumecs) to daily volume in MCM.
    1 m³/s for 1 day (86,400 seconds) = 86,400 m³ = 0.0864 MCM.
    """
    return discharge_cumecs * 86400.0 / 1e6


def mcm_per_day_to_cumecs(volume_mcm: float) -> float:
    """
    Convert daily volume in MCM to average flow rate in m³/s (cumecs).
    """
    return (volume_mcm * 1e6) / 86400.0


def depth_mm_and_area_sqkm_to_volume_mcm(depth_mm: float, area_sqkm: float) -> float:
    """
    Convert precipitation or evaporation depth in mm over surface area in km² to volume in MCM.
    """
    return (depth_mm * area_sqkm) / 1000.0


def volume_mcm_and_area_sqkm_to_depth_mm(volume_mcm: float, area_sqkm: float) -> float:
    """
    Convert volume in MCM over surface area in km² to equivalent depth in mm.
    """
    if area_sqkm <= 0:
        return 0.0
    return (volume_mcm * 1000.0) / area_sqkm


def compute_rmse(observed: np.ndarray, simulated: np.ndarray) -> float:
    """Root Mean Square Error (RMSE)."""
    mask = ~np.isnan(observed) & ~np.isnan(simulated)
    if np.sum(mask) == 0:
        return np.nan
    return float(np.sqrt(np.mean((observed[mask] - simulated[mask]) ** 2)))


def compute_bias(observed: np.ndarray, simulated: np.ndarray) -> float:
    """Mean Bias (simulated - observed)."""
    mask = ~np.isnan(observed) & ~np.isnan(simulated)
    if np.sum(mask) == 0:
        return np.nan
    return float(np.mean(simulated[mask] - observed[mask]))


def compute_nse(observed: np.ndarray, simulated: np.ndarray) -> float:
    """
    Nash-Sutcliffe Efficiency (NSE).
    NSE = 1 - sum((obs - sim)^2) / sum((obs - mean(obs))^2)
    """
    mask = ~np.isnan(observed) & ~np.isnan(simulated)
    if np.sum(mask) == 0:
        return np.nan
    obs_valid = observed[mask]
    sim_valid = simulated[mask]
    obs_mean = np.mean(obs_valid)
    ss_res = np.sum((obs_valid - sim_valid) ** 2)
    ss_tot = np.sum((obs_valid - obs_mean) ** 2)
    if ss_tot == 0:
        return np.nan
    return float(1.0 - (ss_res / ss_tot))
