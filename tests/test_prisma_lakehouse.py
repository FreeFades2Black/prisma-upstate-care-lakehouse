"""
Prisma Health Upstate Regional Care Coordination & Bed-Surge Lakehouse
Test Suite (tests/test_prisma_lakehouse.py)
"""

import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.models import PRISMA_UPSTATE_FACILITIES, FacilityAcuityTier
from src.ingestion.gunfighter_upstate_extractor import GunfighterUpstateExtractor, PRISMA_UPSTATE_CCNS
from src.analytics.transfer_optimizer import UpstateTransferOptimizer
from src.analytics.timesfm_bed_surge_forecast import TimesFM3BedSurgeForecaster
from src.analytics.timesfm_historical_backtest import TimesFM5YearBacktestEngine
from src.processing.delta_lakehouse import PrismaUpstateLakehousePipeline


def test_prisma_ccn_registry_integrity():
    """Verify all 5 real Upstate CMS Certification Numbers are registered with correct clinical focus."""
    assert len(PRISMA_UPSTATE_FACILITIES) == 5
    assert "420078" in PRISMA_UPSTATE_FACILITIES
    assert PRISMA_UPSTATE_FACILITIES["420078"]["is_tertiary_hub"] is True
    assert PRISMA_UPSTATE_FACILITIES["420078"]["total_staffed_beds"] == 814
    assert PRISMA_UPSTATE_FACILITIES["420102"]["facility_name"] == "Prisma Health Patewood Hospital"
    assert PRISMA_UPSTATE_FACILITIES["420015"]["county"] == "Pickens"


def test_bronze_ingestion_and_silver_mart():
    """Verify Bronze ingestion and Silver Delta Care Mart generation."""
    extractor = GunfighterUpstateExtractor()
    raw_csv = extractor.generate_synthetic_cms_feed(days=15)
    bronze_path = extractor.ingest_to_bronze(raw_csv)
    silver_path = extractor.build_silver_mart(bronze_path)

    assert bronze_path.exists()
    assert silver_path.exists()


def test_transfer_optimizer_routing():
    """Verify patient transfer diversion logic relieves Greenville Memorial bottleneck."""
    optimizer = UpstateTransferOptimizer()
    dossier = optimizer.optimize_fleet_capacity()

    assert "tertiary_hub_status" in dossier
    assert dossier["metadata"]["tertiary_hub_ccn"] == "420078"
    assert len(dossier["transfer_routing_recommendations"]) == 4
    assert "annual_projected_savings_usd" in dossier["financial_roi"]


def test_timesfm_bed_surge_forecaster():
    """Verify TimesFM-3 produces 28-day forward forecasts with P10/P50/P90 quantile intervals."""
    forecaster = TimesFM3BedSurgeForecaster()
    dossier = forecaster.generate_surge_forecasts()

    assert "model_metadata" in dossier
    assert len(dossier["facility_forecasts"]) == 5
    
    gvl_forecast = dossier["facility_forecasts"]["420078"]
    assert len(gvl_forecast["28_day_daily_trajectory"]) == 28
    
    # Check quantiles
    for day in gvl_forecast["28_day_daily_trajectory"]:
        p10 = day["confidence_lower_p10"]
        p50 = day["projected_occupancy_pct_p50"]
        p90 = day["confidence_upper_p90"]
        assert p10 <= p50 <= p90


def test_timesfm_5year_historical_backtest():
    """Verify 5-year historical backtest evaluation engine against annual surge episodes."""
    engine = TimesFM5YearBacktestEngine()
    dossier = engine.generate_5yr_backtest_dossier()

    assert "overall_precision_scorecard" in dossier
    assert len(dossier["annual_surge_episodes"]) == 6
    assert len(dossier["monthly_backtest_timeline"]["months"]) == 68

    # Verify high statistical precision across episodes
    for ep in dossier["annual_surge_episodes"]:
        assert ep["error_mape_pct"] < 3.0  # High precision requirement (<3% MAPE)
        assert ep["lead_time_days"] >= 14  # At least 2 weeks early warning lead time


def test_full_medallion_pipeline_execution():
    """Verify end-to-end Medallion lakehouse execution."""
    pipeline = PrismaUpstateLakehousePipeline()
    result = pipeline.run_full_pipeline()
    assert result["pipeline_status"] == "SUCCESS"
