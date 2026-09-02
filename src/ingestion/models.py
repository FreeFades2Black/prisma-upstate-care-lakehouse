"""
Prisma Health Upstate Regional Care Coordination & Bed-Surge Lakehouse
Data Models & Schema Specifications (src/ingestion/models.py)
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class FacilityAcuityTier(str, Enum):
    TERTIARY_LEVEL1_TRAUMA = "TERTIARY_LEVEL1_TRAUMA"
    SPECIALTY_SHORT_STAY = "SPECIALTY_SHORT_STAY"
    COMMUNITY_ACUTE_CARE = "COMMUNITY_ACUTE_CARE"
    RURAL_ADJACENT_FEEDER = "RURAL_ADJACENT_FEEDER"


class PrismaFacilityMetadata(BaseModel):
    ccn: str = Field(..., description="Official CMS Certification Number")
    facility_name: str
    location_label: str
    county: str
    latitude: float
    longitude: float
    total_staffed_beds: int
    total_icu_beds: int
    case_mix_index_cmi: float
    acuity_tier: FacilityAcuityTier
    primary_clinical_focus: str
    is_tertiary_hub: bool = False


# Official CMS CCN registry for Prisma Health Upstate facilities
PRISMA_UPSTATE_FACILITIES: Dict[str, Dict[str, Any]] = {
    "420078": {
        "ccn": "420078",
        "facility_name": "Prisma Health Greenville Memorial Hospital",
        "location_label": "Greenville, SC (Grove Rd)",
        "county": "Greenville",
        "latitude": 34.8214,
        "longitude": -82.4147,
        "total_staffed_beds": 814,
        "total_icu_beds": 112,
        "case_mix_index_cmi": 2.18,
        "acuity_tier": FacilityAcuityTier.TERTIARY_LEVEL1_TRAUMA,
        "primary_clinical_focus": "Level 1 Trauma, Tertiary Referral, High CMI, Cardiovascular & Neuro ICU",
        "is_tertiary_hub": True
    },
    "420102": {
        "ccn": "420102",
        "facility_name": "Prisma Health Patewood Hospital",
        "location_label": "Greenville, SC (Patewood Dr)",
        "county": "Greenville",
        "latitude": 34.8569,
        "longitude": -82.3168,
        "total_staffed_beds": 72,
        "total_icu_beds": 8,
        "case_mix_index_cmi": 1.25,
        "acuity_tier": FacilityAcuityTier.SPECIALTY_SHORT_STAY,
        "primary_clinical_focus": "Short-Stay Elective Surgery, Orthopedics, Women's Health & Low-Acuity Medical",
        "is_tertiary_hub": False
    },
    "420033": {
        "ccn": "420033",
        "facility_name": "Prisma Health Greer Memorial Hospital",
        "location_label": "Greer, SC",
        "county": "Greenville",
        "latitude": 34.9452,
        "longitude": -82.2384,
        "total_staffed_beds": 82,
        "total_icu_beds": 10,
        "case_mix_index_cmi": 1.42,
        "acuity_tier": FacilityAcuityTier.COMMUNITY_ACUTE_CARE,
        "primary_clinical_focus": "Community Acute Care, General Inpatient, Regional Transfer Diversion Target",
        "is_tertiary_hub": False
    },
    "420037": {
        "ccn": "420037",
        "facility_name": "Prisma Health Hillcrest Hospital",
        "location_label": "Simpsonville, SC",
        "county": "Greenville",
        "latitude": 34.7237,
        "longitude": -82.2612,
        "total_staffed_beds": 48,
        "total_icu_beds": 6,
        "case_mix_index_cmi": 1.31,
        "acuity_tier": FacilityAcuityTier.COMMUNITY_ACUTE_CARE,
        "primary_clinical_focus": "Community Acute Care, Outpatient / ER Feeder, Low-Acuity Inpatient Recovery",
        "is_tertiary_hub": False
    },
    "420015": {
        "ccn": "420015",
        "facility_name": "Prisma Health Baptist Easley Hospital",
        "location_label": "Easley, SC",
        "county": "Pickens",
        "latitude": 34.8385,
        "longitude": -82.6074,
        "total_staffed_beds": 109,
        "total_icu_beds": 12,
        "case_mix_index_cmi": 1.38,
        "acuity_tier": FacilityAcuityTier.RURAL_ADJACENT_FEEDER,
        "primary_clinical_focus": "Acute Care / Rural-Adjacent Pickens County Feeder & Sub-Acute Transition",
        "is_tertiary_hub": False
    }
}


class DailyBedTelemetryRecord(BaseModel):
    timestamp_utc: str
    date: str
    ccn: str
    facility_name: str
    occupied_med_surg_beds: int
    available_med_surg_beds: int
    occupied_icu_beds: int
    available_icu_beds: int
    occupancy_rate_pct: float
    er_wait_time_minutes: int
    diverted_transfers_today: int
    incoming_transfer_requests: int
    flu_rsv_covid_admissions: int
    bed_surge_pressure_index: float  # 0.0 to 100.0
    status_directive: str  # NORMAL, ADVISORY, TRANSFER_ACTIVE, CODE_PURPLE_CRUNCH
