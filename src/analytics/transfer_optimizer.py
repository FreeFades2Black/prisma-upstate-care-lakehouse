"""
Prisma Health Upstate Regional Care Coordination & Bed-Surge Lakehouse
Upstate Regional Transfer & Capacity Balancing Optimization Engine
(src/analytics/transfer_optimizer.py)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
GOLD_DIR.mkdir(parents=True, exist_ok=True)


class UpstateTransferOptimizer:
    """Optimizes patient transfers from Greenville Memorial (420078) to Upstate satellites."""

    TRANSFER_CORRIDORS = [
        {
            "target_ccn": "420102",
            "target_facility": "Prisma Health Patewood Hospital",
            "target_location": "Greenville, SC (Patewood Dr)",
            "driving_distance_miles": 6.8,
            "transport_time_minutes": 14,
            "eligible_acuity_types": ["Elective Post-Surgical", "Orthopedic Recovery", "Low-Acuity Observation"],
            "max_daily_inflow": 12
        },
        {
            "target_ccn": "420033",
            "target_facility": "Prisma Health Greer Memorial Hospital",
            "target_location": "Greer, SC",
            "driving_distance_miles": 14.2,
            "transport_time_minutes": 22,
            "eligible_acuity_types": ["General Medical Inpatient", "Sub-Acute Respiratory Stepdown", "Stable Telemetry"],
            "max_daily_inflow": 14
        },
        {
            "target_ccn": "420037",
            "target_facility": "Prisma Health Hillcrest Hospital",
            "target_location": "Simpsonville, SC",
            "driving_distance_miles": 16.5,
            "transport_time_minutes": 24,
            "eligible_acuity_types": ["Low-Acuity Medical Recovery", "Observation", "Rehab Transition"],
            "max_daily_inflow": 8
        },
        {
            "target_ccn": "420015",
            "target_facility": "Prisma Health Baptist Easley Hospital",
            "target_location": "Easley, SC (Pickens Co.)",
            "driving_distance_miles": 12.8,
            "transport_time_minutes": 19,
            "eligible_acuity_types": ["Pickens Resident Stepdown", "Geriatric Sub-Acute", "General Med-Surg"],
            "max_daily_inflow": 10
        }
    ]

    def optimize_fleet_capacity(self) -> Dict[str, Any]:
        """Calculates real-time transfer recommendations, load shedding, and financial ROI."""
        silver_file = SILVER_DIR / "silver_upstate_care_mart.json"
        with open(silver_file, "r", encoding="utf-8") as f:
            silver_records = json.load(f)

        # Grab latest daily snapshot per CCN
        latest_by_ccn = {}
        for r in silver_records:
            ccn = r["ccn"]
            if ccn not in latest_by_ccn or r["date"] > latest_by_ccn[ccn]["date"]:
                latest_by_ccn[ccn] = r

        gvl_memorial = latest_by_ccn["420078"]
        gvl_occ = gvl_memorial["occupancy_rate_pct"]
        gvl_er_wait = gvl_memorial["er_wait_time_minutes"]

        # Calculate excess patient volume needing load-shedding
        is_crunch = gvl_occ > 88.0
        excess_patients = max(0, int((gvl_occ - 85.0) * (gvl_memorial["total_staffed_beds"] / 100.0))) if is_crunch else 0

        recommended_transfers = []
        allocated_count = 0

        for corridor in self.TRANSFER_CORRIDORS:
            t_ccn = corridor["target_ccn"]
            t_data = latest_by_ccn[t_ccn]
            t_avail = t_data["available_med_surg_beds"]
            t_occ = t_data["occupancy_rate_pct"]

            # Transfer allocation logic
            if excess_patients > 0 and t_avail > 2 and t_occ < 85.0:
                transfer_quota = min(corridor["max_daily_inflow"], t_avail - 2, excess_patients - allocated_count)
                allocated_count += transfer_quota
            else:
                transfer_quota = 0

            recommended_transfers.append({
                "destination_ccn": t_ccn,
                "destination_name": corridor["target_facility"],
                "destination_location": corridor["target_location"],
                "distance_from_grove_rd_miles": corridor["driving_distance_miles"],
                "transit_time_minutes": corridor["transport_time_minutes"],
                "current_occupancy_pct": t_occ,
                "available_beds": t_avail,
                "recommended_transfers_today": transfer_quota,
                "eligible_acuity_types": corridor["eligible_acuity_types"],
                "routing_status": "ACTIVE_TRANSFER_CORRIDOR" if transfer_quota > 0 else "STANDBY_CAPACITY"
            })

        # Calculate Financial & Clinical Value Realization
        # At $1,850 per delayed boarding day and avoided ER diversion penalties ($42,000/shift)
        daily_savings_usd = allocated_count * 1850 + (42000 if allocated_count > 10 else 0)
        annual_projected_savings_usd = daily_savings_usd * 365

        dossier = {
            "metadata": {
                "engine": "Prisma-Upstate-Care-Coordination-Optimizer",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "tertiary_hub_ccn": "420078",
                "tertiary_hub_name": "Prisma Health Greenville Memorial Hospital"
            },
            "tertiary_hub_status": {
                "occupancy_rate_pct": gvl_occ,
                "er_wait_time_minutes": gvl_er_wait,
                "status_directive": gvl_memorial["status_directive"],
                "bed_surge_pressure_index": gvl_memorial["bed_surge_pressure_index"],
                "excess_patient_load": excess_patients,
                "transfers_dispatched": allocated_count
            },
            "transfer_routing_recommendations": recommended_transfers,
            "financial_roi": {
                "daily_avoided_boarding_cost_usd": f"${daily_savings_usd:,.2f}",
                "annual_projected_savings_usd": f"${annual_projected_savings_usd:,.2f}",
                "er_bottleneck_hours_reduced": round(allocated_count * 2.8, 1)
            }
        }

        gold_file = GOLD_DIR / "gold_transfer_optimization.json"
        with open(gold_file, "w", encoding="utf-8") as f:
            json.dump(dossier, f, indent=2)

        print(f"Generated Gold Transfer Optimization Dossier: {gold_file}")
        return dossier


if __name__ == "__main__":
    optimizer = UpstateTransferOptimizer()
    optimizer.optimize_fleet_capacity()
