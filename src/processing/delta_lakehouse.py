"""
Prisma Health Upstate Regional Care Coordination & Bed-Surge Lakehouse
End-to-End Medallion Delta Lakehouse Pipeline (src/processing/delta_lakehouse.py)
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.gunfighter_upstate_extractor import GunfighterUpstateExtractor
from src.analytics.transfer_optimizer import UpstateTransferOptimizer
from src.analytics.timesfm_bed_surge_forecast import TimesFM3BedSurgeForecaster


class PrismaUpstateLakehousePipeline:
    """Orchestrates Bronze Ingestion -> Silver Care Mart -> Gold TimesFM Forecasting."""

    def __init__(self):
        self.extractor = GunfighterUpstateExtractor()
        self.optimizer = UpstateTransferOptimizer()
        self.forecaster = TimesFM3BedSurgeForecaster()

    def run_full_pipeline(self) -> Dict[str, Any]:
        print("=== Executing Prisma Upstate Medallion Lakehouse Pipeline ===")
        
        # 1. Bronze Layer Ingestion
        print("[1/3] Ingesting Federal CMS & Upstate Viral Surveillance to Bronze...")
        raw_csv = self.extractor.generate_synthetic_cms_feed()
        bronze_path = self.extractor.ingest_to_bronze(raw_csv)

        # 2. Silver Layer Normalization & Facility Tagging
        print("[2/3] Processing Silver Upstate Care Coordination Mart...")
        silver_path = self.extractor.build_silver_mart(bronze_path)

        # 3. Gold Layer Analytics & TimesFM-3 Foundation Forecasting
        print("[3/3] Executing Gold TimesFM-3 28-Day Bed Surge & Transfer Optimization...")
        transfer_dossier = self.optimizer.optimize_fleet_capacity()
        surge_dossier = self.forecaster.generate_surge_forecasts()

        summary = {
            "pipeline_status": "SUCCESS",
            "bronze_records": bronze_path.name,
            "silver_mart": silver_path.name,
            "gold_transfer_optimization": "gold_transfer_optimization.json",
            "gold_timesfm_forecast": "gold_timesfm_bed_surge_forecast.json",
            "tertiary_hub": "Prisma Health Greenville Memorial Hospital (CCN: 420078)",
            "annual_projected_savings": transfer_dossier["financial_roi"]["annual_projected_savings_usd"]
        }
        print("=== Medallion Lakehouse Execution Complete ===")
        return summary


if __name__ == "__main__":
    pipeline = PrismaUpstateLakehousePipeline()
    pipeline.run_full_pipeline()
