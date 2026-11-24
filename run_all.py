"""
CE 766 Ujjani Reservoir Water Balance Model
Master Reproducibility Script: run_all.py
Purpose: Sequentially executes all data cleaning, curve fitting, simulation,
         calibration/validation, intervention evaluation, sensitivity analysis,
         and figure generation scripts end-to-end.
"""

import subprocess
import sys
import time

SCRIPTS = [
    ("Phase 2: Clean & Aggregate Data", "src/01_clean_data.py"),
    ("Phase 3: Elevation-Area-Capacity Curve", "src/02_storage_curve.py"),
    ("Phase 4: Water Balance Model Test", "src/03_water_balance.py"),
    ("Phase 5: Calibration & Validation", "src/04_calibrate_validate.py"),
    ("Phase 6 & 7: Policy Interventions Simulation", "src/05_interventions.py"),
    ("Phase 7 (OAT Sensitivity Analysis)", "src/07_sensitivity_analysis.py"),
    ("Phase 8: Generate Publication Figures", "src/06_make_figures.py"),
]


def main():
    print("=" * 70)
    print("CE 766 Ujjani Reservoir Water Balance Model: Full Execution Pipeline")
    print("=" * 70)
    start_total = time.time()

    for desc, script_path in SCRIPTS:
        print(f"\n>> Executing: {desc} ({script_path})...")
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[FAILED] Error executing {script_path}:")
            print(res.stderr)
            sys.exit(res.returncode)
        else:
            print(res.stdout.strip())
            print(f"[OK] {script_path} completed successfully.")

    total_time = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"All scripts executed successfully in {total_time:.2f} seconds.")
    print("All processed datasets, tables, and 200 DPI figures are up-to-date.")
    print("=" * 70)


if __name__ == "__main__":
    main()
