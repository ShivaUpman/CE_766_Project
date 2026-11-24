# CE 766 Project: Water Balance Modeling and Policy Intervention Evaluation for Ujjani Reservoir

[![Course](https://img.shields.io/badge/Course-CE%20766%20Watershed%20Management-blue.svg)](https://www.civil.iitb.ac.in/)
[![Institution](https://img.shields.io/badge/IIT%20Bombay-Department%20of%20Civil%20Engineering-darkred.svg)](https://www.iitb.ac.in/)
[![Analysis Period](https://img.shields.io/badge/Period-2021--2025-green.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

This repository contains the complete dataset, simulation model, empirical calibration-validation framework, and policy intervention analysis for **Ujjani Reservoir** (Bhima River, Solapur district, Maharashtra, India) for the 5-year hydrological period **1 January 2021 to 31 December 2025**.

---

## 1. Research Question & Scope
> **Did historical releases balance irrigation delivery and reservoir security, and would 3–4 realistic alternative management interventions have performed better under the observed hydrology?**

In direct response to preliminary feedback, this project emphasizes:
- **Zero data fabrication**: All numbers trace to published government data portals (NWIC, NWDP, CWC, MWRRA).
- **Physical mass conservation**: Daily lumped reservoir mass-balance model with cubic spline Elevation-Area-Capacity interpolation.

---

## 2. Directory Structure
```
CE766 Project/
├── run_all.py                      # Master execution script (reproduces everything in ~10 seconds)
├── requirements.txt                # Minimal dependencies (pandas, numpy, scipy, matplotlib)
├── data/
│   ├── raw/                        # Read-only raw datasets from NWIC, CWC, NWDP
│   └── processed/                  # Contiguous daily hydrometeorology & simulation time series
├── src/
│   ├── 00_download_data.py         # Autonomous dataset retrieval
│   ├── 01_clean_data.py            # Quality control, parsing, and daily aggregation
│   ├── 02_storage_curve.py         # Elevation-Area-Capacity spline modeling
│   ├── 03_water_balance.py         # Daily lumped water-balance simulation engine
│   ├── 04_calibrate_validate.py    # Calibration (2021–2023) and validation (2024–2025)
│   ├── 05_interventions.py         # Simulation of Baseline + 3 policy interventions
│   ├── 06_make_figures.py          # Generates publication-ready figures (200 DPI)
│   ├── 07_sensitivity_analysis.py  # One-At-A-Time (OAT) parameter sensitivity analysis
│   └── utils.py                    # Unit conversions, storage functions, and evaluation metrics
├── results/
│   ├── figures/                    # Visual 1 (calibration/validation) & Visual 2 (interventions)
│   └── tables/                     # Summary CSV tables (metrics, interventions, sensitivity)
├── docs/
│   ├── assumptions_log.md          # Log of all scientific assumptions and data gap handlings
│   ├── progress_log.md             # Running chronological log of project activities
│   ├── data_sources.md             # Data URLs, citations, and access timestamps
│   ├── data_dictionary.md          # Variable names, units, and descriptions
│   └── explain_for_quiz.md         # Plain-English technical explanations for oral quiz defense
└── report/
    ├── preliminary_update.md       # Preliminary submission document
    └── final_report.md             # Comprehensive final report
```

---

## 3. Quickstart & Reproducibility
Clone the repository and run the full pipeline in one command:
```bash
git clone https://github.com/ShivaUpman/CE_766_Project.git
cd CE_766_Project
pip install -r requirements.txt
python run_all.py
```

---

## 4. Key Quantitative Results

### Calibration and Validation Performance
- **Calibration (2021–2023, 1,095 days)**: $\text{NSE} = 1.000, \text{RMSE} = 5.65\text{ MCM}, \text{Mean Bias} = +0.02\text{ MCM}$
- **Validation (2024–2025, 731 days)**: $\text{NSE} = 0.999, \text{RMSE} = 12.53\text{ MCM}, \text{Mean Bias} = -0.02\text{ MCM}$

### Policy Interventions Summary (2021–2025)
| Scenario | Total Delivered (MCM) | Irrigation Deficit (MCM) | Shortfall Rate (%) | Minimum Storage (MCM) | Mean June 1 Carryover (MCM) | Days Below MDDL (Dead Storage) | Total Spill (MCM) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline (Historical)** | 7,065.1 | 133.1 | 1.8% | 1,779.7 | 1,960.7 | 34 | 6,200.0 |
| **L1: Drought Hedging** (20% cut < 25% live storage) | 6,800.8 | 397.4 | 5.5% | 1,801.2 | 1,997.4 | 3 | 6,379.5 |
| **L2: Canal Modernization** (15% loss reduction) | 6,118.5 | 0.0 | 0.0% | 1,924.2 | 2,148.5 | 0 | 7,007.7 |
| **L3: Pre-Monsoon Flood Cushion** (40% headroom) | 7,065.1 | 133.1 | 1.8% | 1,779.7 | 2,005.2 | 34 | 5,045.6 |

---

## 5. Visuals
- **Figure 1 (Visual 1)**: `results/figures/figure1_model_calibration_validation.png` (Hydrologic forcing & calibrated vs validated reservoir storage).
- **Figure 2 (Visual 2)**: `results/figures/figure2_interventions_tradeoffs.png` (Multi-year storage trajectories and trade-off comparison).

---

## 6. Primary References
1. **Central Water Commission (CWC)** (2020). *Sedimentation Assessment of Ujjani Reservoir through Satellite Remote Sensing (SRS)*. Remote Sensing Directorate, Ministry of Jal Shakti, New Delhi.
2. **Maharashtra Water Resources Regulatory Authority (MWRRA)** (2015). *Regulatory Order on Equitable Distribution of Water in the Bhima Sub-Basin, Case No. 14 of 2015*, Mumbai.
3. **Loucks, D. P., & van Beek, E.** (2017). *Water Resource Systems Planning and Management: An Introduction to Methods, Models, and Applications*. Springer, Cham.
