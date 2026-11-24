"""
CE 766 Ujjani Reservoir Water Balance Model
Script: 00_download_data.py
Purpose: Download raw hydrometeorological and reservoir operational data
         from the National Water Data Portal (NWDP / NWIC) CKAN repository.
Inputs:  Remote CKAN endpoints on https://nwdp.nwic.gov.in
Outputs: CSV files saved to data/raw/
"""

import os
import ssl
import urllib.request

DATA_URLS = {
    # 1. Dam spillway gate discharge (cusecs)
    "reservior_discharge_tel_hr_maharashtra_sw_mh_ujjani_dam_1_2021_2025.csv": (
        "https://nwdp.nwic.gov.in/dataset/a0c6fb7a-cc0d-4c1b-be0f-9ba974c42164/resource/"
        "bb63b1bb-76df-4bbe-8cb9-60313254ccb3/download/"
        "reservior_discharge_tel_hr_maharashtra_sw_mh_ujjani_dam_1_2021_2025.csv"
    ),
    # 2. Main canal head regulator discharge (cusecs)
    "reservior_discharge_tele_hr_maharashtra-sw_mh_ujjani-dam-head-regulator-canal_2021_2025.csv": (
        "https://nwdp.nwic.gov.in/dataset/7481ab9f-c8d2-42a9-82ae-a88496c90568/resource/"
        "3dd3a41c-b434-413a-9600-1f6266435bbc/download/"
        "reservior_discharge_tele_hr_maharashtra-sw_mh_ujjani-dam-head-regulator-canal_2021_2025.csv"
    ),
    # 3. Bhima-Sina link canal discharge (cusecs)
    "reservior_discharge_tel_hr_maharashtra_sw_mh_bhima-sina_link_canal_2021_2025.csv": (
        "https://nwdp.nwic.gov.in/dataset/f4fc96a5-016a-4cb9-a21d-0a73dc3fbc9b/resource/"
        "5df797f1-d326-4102-9a3f-da84176fbe6a/download/"
        "reservior_discharge_tel_hr_maharashtra_sw_mh_bhima-sina_link_canal_2021_2025.csv"
    ),
    # 4. Rain gauge telemetry
    "reservior_discharge_tele_hr_maharashtra-sw_mh_ujjani-dam-rain-gauge_2021_2025.csv": (
        "https://nwdp.nwic.gov.in/dataset/6de0db8d-b67d-4165-824d-80c00c07aa01/resource/"
        "4f40b76d-86c8-498a-9ca4-5abc7b65a532/download/"
        "reservior_discharge_tele_hr_maharashtra-sw_mh_ujjani-dam-rain-gauge_2021_2025.csv"
    ),
    # 5. CWC Manual Daily Rainfall for Maharashtra (including Ujjani Reservoir station 2021-2025)
    "rainfall_manual_daily_cwc_mh_2021_2025.csv": (
        "https://nwdp.nwic.gov.in/dataset/3b2b3516-f115-4c98-a11c-9ee7406147f2/resource/"
        "1d7a5f00-64a9-484d-a1fa-f77a8ad3f23d/download/"
        "rainfall_manual_daily_cwc_mh_2021_2025.csv"
    )
}


def download_all(dest_dir: str = "data/raw") -> None:
    os.makedirs(dest_dir, exist_ok=True)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0"}

    for filename, url in DATA_URLS.items():
        target_path = os.path.join(dest_dir, filename)
        if os.path.exists(target_path):
            size_mb = os.path.getsize(target_path) / (1024 * 1024)
            print(f"[SKIP] {filename} already exists ({size_mb:.2f} MB).")
            continue

        print(f"[DOWNLOADING] {filename} from NWDP...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
                data = resp.read()
                with open(target_path, "wb") as f:
                    f.write(data)
            size_mb = len(data) / (1024 * 1024)
            print(f"[SUCCESS] Saved {filename} ({size_mb:.2f} MB).")
        except Exception as e:
            print(f"[ERROR] Failed to download {filename}: {e}")


if __name__ == "__main__":
    download_all()
