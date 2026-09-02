"""
Prisma Health Upstate Regional Care Coordination & Bed-Surge Lakehouse
Gunfighter Upstate Ingestion & Delta Extraction Engine
(src/ingestion/gunfighter_upstate_extractor.py)

The Gunslinger rides the ridgeline of the Blue Ridge foothills,
sorting the brands of the Upstate herds before the storm breaks over Grove Road.
"""

import json
import os
import csv
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.models import PRISMA_UPSTATE_FACILITIES, DailyBedTelemetryRecord

CMS_RAW_DIR = PROJECT_ROOT / "data" / "cms_raw"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

CMS_RAW_DIR.mkdir(parents=True, exist_ok=True)
BRONZE_DIR.mkdir(parents=True, exist_ok=True)
SILVER_DIR.mkdir(parents=True, exist_ok=True)

# Official CMS CCN keys for Prisma Health Upstate facilities
PRISMA_UPSTATE_CCNS = {
    "420078": "Prisma Health Greenville Memorial Hospital",
    "420102": "Prisma Health Patewood Hospital",
    "420033": "Prisma Health Greer Memorial Hospital",
    "420037": "Prisma Health Hillcrest Hospital",
    "420015": "Prisma Health Baptist Easley Hospital"
}


class GunfighterUpstateExtractor:
    """Ingests federal CMS hospital compare datasets and Upstate surveillance ledgers into Delta Lake."""

    def __init__(self, use_pyspark: bool = False):
        self.use_pyspark = use_pyspark
        self.spark = None
        if self.use_pyspark:
            try:
                from pyspark.sql import SparkSession
                self.spark = SparkSession.builder \
                    .appName("Gunslinger-Prisma-Upstate-ETL") \
                    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                    .getOrCreate()
            except ImportError:
                self.spark = None

    def generate_synthetic_cms_feed(self, days: int = 60) -> Path:
        """Generates historical 60-day CMS and CDC respiratory surveillance telemetry for Upstate SC."""
        feed_file = CMS_RAW_DIR / "upstate_cms_hospital_telemetry.csv"
        now = datetime.now(timezone.utc)

        headers = [
            "timestamp_utc", "date", "Facility ID", "Facility Name", "State", "County",
            "Staffed Beds", "ICU Beds", "Occupied MedSurg", "Occupied ICU",
            "ER Wait Mins", "Diverted Transfers", "Incoming Transfer Requests",
            "Flu RSV COVID Admissions", "Case Mix Index"
        ]

        rows = []
        for day_idx in range(days, -1, -1):
            dt = now - timedelta(days=day_idx)
            date_str = dt.strftime("%Y-%m-%d")
            
            # Seasonal respiratory surge wave (peaks towards winter / current month)
            seasonal_surge = 1.0 + 0.35 * (1.0 - (day_idx / max(1, days)))

            for ccn, meta in PRISMA_UPSTATE_FACILITIES.items():
                total_beds = meta["total_staffed_beds"]
                total_icu = meta["total_icu_beds"]
                is_hub = meta["is_tertiary_hub"]

                # Greenville Memorial carries high occupancy and bottlenecking
                base_occ = 0.92 if is_hub else 0.72
                occ_rate = min(0.99, base_occ * seasonal_surge * (0.95 + (hash(f"{ccn}-{day_idx}") % 10) / 100.0))
                
                occupied_med = int((total_beds - total_icu) * occ_rate)
                occupied_icu = int(total_icu * min(0.98, occ_rate * 1.05))
                er_wait = int(85 * occ_rate * (1.6 if is_hub else 0.8))
                
                diverted = int(6 * seasonal_surge) if is_hub and occ_rate > 0.90 else 0
                incoming_transfers = int(24 * seasonal_surge) if is_hub else int(4 * seasonal_surge)
                viral_adm = int(14 * seasonal_surge) if is_hub else int(3 * seasonal_surge)

                rows.append([
                    dt.isoformat(),
                    date_str,
                    ccn,
                    meta["facility_name"],
                    "SC",
                    meta["county"],
                    total_beds,
                    total_icu,
                    occupied_med,
                    occupied_icu,
                    er_wait,
                    diverted,
                    incoming_transfers,
                    viral_adm,
                    meta["case_mix_index_cmi"]
                ])

        with open(feed_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        print(f"Generated Raw CMS Upstate Telemetry Feed: {feed_file} ({len(rows)} records)")
        return feed_file

    def ingest_to_bronze(self, raw_csv_path: Optional[Path] = None) -> Path:
        """Raw ingestion dropped off the stagecoach into Bronze Lakehouse."""
        if raw_csv_path is None:
            raw_csv_path = self.generate_synthetic_cms_feed()

        bronze_file = BRONZE_DIR / "bronze_cms_upstate_records.json"
        records = []
        with open(raw_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                records.append({
                    "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
                    "facility_id": r["Facility ID"],
                    "facility_name": r["Facility Name"],
                    "state": r["State"],
                    "county": r["County"],
                    "staffed_beds": int(r["Staffed Beds"]),
                    "icu_beds": int(r["ICU Beds"]),
                    "occupied_med_surg": int(r["Occupied MedSurg"]),
                    "occupied_icu": int(r["Occupied ICU"]),
                    "er_wait_mins": int(r["ER Wait Mins"]),
                    "diverted_transfers": int(r["Diverted Transfers"]),
                    "incoming_transfers": int(r["Incoming Transfer Requests"]),
                    "viral_admissions": int(r["Flu RSV COVID Admissions"]),
                    "case_mix_index": float(r["Case Mix Index"]),
                    "date": r["date"],
                    "timestamp_utc": r["timestamp_utc"]
                })

        with open(bronze_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

        print(f"Ingested Bronze Delta Lakehouse Vault: {bronze_file} ({len(records)} entries)")
        return bronze_file

    def build_silver_mart(self, bronze_path: Optional[Path] = None) -> Path:
        """Silver Layer: Normalization, SCD-2 partition labeling, and Tertiary Hub tagging."""
        if bronze_path is None:
            bronze_path = BRONZE_DIR / "bronze_cms_upstate_records.json"

        with open(bronze_path, "r", encoding="utf-8") as f:
            bronze_records = json.load(f)

        silver_records = []
        target_ccn_list = set(PRISMA_UPSTATE_CCNS.keys())

        for r in bronze_records:
            ccn = r["facility_id"]
            if r["state"] == "SC" and ccn in target_ccn_list:
                meta = PRISMA_UPSTATE_FACILITIES[ccn]
                total_beds = meta["total_staffed_beds"]
                occupied_total = r["occupied_med_surg"] + r["occupied_icu"]
                occupancy_rate = round((occupied_total / max(1, total_beds)) * 100.0, 2)
                
                # Bed surge pressure index calculation (0-100)
                surge_index = min(100.0, round(occupancy_rate * 0.7 + (r["er_wait_mins"] / 120.0) * 30.0, 1))

                status_directive = (
                    "CODE_PURPLE_CRUNCH" if surge_index >= 90.0 or occupancy_rate >= 94.0
                    else "TRANSFER_DIVERSION_ACTIVE" if surge_index >= 80.0
                    else "ADVISORY_MONITORING" if surge_index >= 70.0
                    else "NORMAL_OPERATIONS"
                )

                silver_records.append({
                    "ccn": ccn,
                    "facility_name": r["facility_name"],
                    "system_network": "Prisma Health Upstate",
                    "location_label": meta["location_label"],
                    "county": meta["county"],
                    "is_tertiary_hub": (ccn == "420078"),
                    "acuity_tier": meta["acuity_tier"].value,
                    "case_mix_index_cmi": meta["case_mix_index_cmi"],
                    "total_staffed_beds": total_beds,
                    "total_icu_beds": meta["total_icu_beds"],
                    "occupied_med_surg_beds": r["occupied_med_surg"],
                    "available_med_surg_beds": total_beds - meta["total_icu_beds"] - r["occupied_med_surg"],
                    "occupied_icu_beds": r["occupied_icu"],
                    "available_icu_beds": meta["total_icu_beds"] - r["occupied_icu"],
                    "occupancy_rate_pct": occupancy_rate,
                    "er_wait_time_minutes": r["er_wait_mins"],
                    "diverted_transfers_today": r["diverted_transfers"],
                    "incoming_transfer_requests": r["incoming_transfers"],
                    "flu_rsv_covid_admissions": r["viral_admissions"],
                    "bed_surge_pressure_index": surge_index,
                    "status_directive": status_directive,
                    "date": r["date"],
                    "timestamp_utc": r["timestamp_utc"]
                })

        silver_file = SILVER_DIR / "silver_upstate_care_mart.json"
        with open(silver_file, "w", encoding="utf-8") as f:
            json.dump(silver_records, f, indent=2)

        print(f"Created Silver Upstate Care Mart: {silver_file} ({len(silver_records)} records)")
        return silver_file


if __name__ == "__main__":
    extractor = GunfighterUpstateExtractor()
    extractor.generate_synthetic_cms_feed()
    b_file = extractor.ingest_to_bronze()
    extractor.build_silver_mart(b_file)
