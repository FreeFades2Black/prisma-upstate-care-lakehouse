# 🏥 Prisma Health Upstate Regional Care Coordination & Bed-Surge Lakehouse

[![Live Executive Showcase](https://img.shields.io/badge/Live%20Showcase-GitHub%20Pages-blue?style=for-the-badge&logo=githubpages&logoColor=white)](https://freefades2black.github.io/prisma-upstate-care-lakehouse/)
[![CMS CCN Keyed](https://img.shields.io/badge/Federal%20CMS-CCN%20Keyed-emerald?style=for-the-badge&logo=medicare&logoColor=white)](https://freefades2black.github.io/prisma-upstate-care-lakehouse/)
[![Google TimesFM-3](https://img.shields.io/badge/Google%20TimesFM--3-Bed%20Surge%20AI-purple?style=for-the-badge&logo=google&logoColor=white)](https://freefades2black.github.io/prisma-upstate-care-lakehouse/)
[![Omarchy Edge AI Node](https://img.shields.io/badge/Omarchy%20Edge%20Node-Bare--Metal%20Arch-cyan?style=for-the-badge&logo=archlinux&logoColor=white)](https://freefades2black.github.io/prisma-upstate-care-lakehouse/)
[![Databricks Delta Lake](https://img.shields.io/badge/Databricks-Delta%20Lake-E25A1C?style=for-the-badge&logo=databricks&logoColor=white)](https://freefades2black.github.io/prisma-upstate-care-lakehouse/)

> ### 🌐 [Click Here to Open the Live Upstate Regional Care Coordination Dashboard ➔](https://freefades2black.github.io/prisma-upstate-care-lakehouse/)
> **Live Zero-Install Visualizer:** Interactive Upstate SC hospital map with real CMS CCN keys, transfer vectors from Grove Road to regional satellites, and 28-day Google TimesFM-3 bed surge forecasts.

---

## 🏛️ Executive Briefing: The Upstate Capacity & Throughput Challenge

In large integrated delivery networks like **Prisma Health Upstate**, managing acute bed capacity is a multi-million-dollar operational challenge. **Prisma Health Greenville Memorial Hospital (`420078`)** on Grove Road operates as the region's sole Level 1 Trauma and tertiary academic medical center, carrying an elevated **Case Mix Index (CMI: 2.18)**.

```
                               ┌────────────────────────────────────────────────────────┐
                               │  PRISMA HEALTH GREENVILLE MEMORIAL HOSPITAL (420078)   │
                               │  Tertiary Hub • Level 1 Trauma • High CMI Bottleneck   │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                       ┌──────────────────────────────────┼─────────────────────────────────┐
                       │ (Transfer Corridor 1)            │ (Transfer Corridor 2)           │ (Transfer Corridor 3)
                       ▼                                  ▼                                 ▼
         ┌───────────────────────────┐      ┌───────────────────────────┐     ┌───────────────────────────┐
         │     PATEWOOD HOSPITAL     │      │   GREER MEMORIAL HOSP.    │     │   BAPTIST EASLEY HOSP.    │
         │       (CCN: 420102)       │      │       (CCN: 420033)       │     │       (CCN: 420015)       │
         │ Ortho / Short-Stay Surg.  │      │  Community Acute Inflow   │     │  Pickens County Feeder    │
         └───────────────────────────┘      └───────────────────────────┘     └───────────────────────────┘
```

When Greenville Memorial enters capacity crunches (>90% occupancy), emergency department boarding times spike, leading to costly ambulance diversions and delayed surgical admissions. 

This Lakehouse solves the bottleneck by:
1. Ingesting federal CMS quality and occupancy data keyed directly by official **CMS Certification Numbers (CCN)**.
2. Modeling automated **load-shedding transfer pathways** to satellite facilities like **Patewood (`420102`)**, **Greer (`420033`)**, **Hillcrest (`420037`)**, and **Baptist Easley (`420015`)**.
3. Forecasting **7-to-28-day forward bed surge demands** using **Google TimesFM-3** correlated with CDC/DHEC viral surveillance (Flu, COVID-19, RSV) to proactively balance beds before emergency departments overflow.

---

## 🏥 Upstate Target Facility Mapping (Official CMS CCN Keys)

Every CMS dataset (*Hospital Compare, Inpatient Prospective Payment System [IPPS], and Quality Payment Program [QPP]*) joins on CMS Certification Numbers (CCN):

| Facility Name | Location | CMS CCN | Staffed Beds | ICU Beds | CMI | Primary Clinical Focus | Role in Lakehouse |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Prisma Health Greenville Memorial Hospital** | Greenville (Grove Rd) | `420078` | **814** | 112 | 2.18 | Level 1 Trauma, Tertiary Referral, High CMI | **Central Tertiary Hub (Load-Shedding Origin)** |
| **Prisma Health Patewood Hospital** | Greenville (Patewood Dr) | `420102` | **72** | 8 | 1.25 | Short-stay surgery, Orthopedics, Women's | **Elective Surgical & Low-Acuity Diversion** |
| **Prisma Health Greer Memorial Hospital** | Greer, SC | `420033` | **82** | 10 | 1.42 | Community Acute Care, Regional Transfer In | **Sub-Acute & Inpatient Medical Diversion** |
| **Prisma Health Hillcrest Hospital** | Simpsonville, SC | `420037` | **48** | 6 | 1.31 | Community Acute Care, Outpatient / ER | **Observation & Low-Acuity Recovery** |
| **Prisma Health Baptist Easley Hospital** | Easley, SC (Pickens Co.) | `420015` | **109** | 12 | 1.38 | Acute Care / Rural-Adjacent Feeder | **Pickens Regional Feeder & Stepdown** |

---

## 🔮 Google TimesFM-3 Foundation Bed-Surge Forecasting

Traditional hospital surge models rely on basic rolling moving averages that fail to anticipate non-linear viral outbreaks and day-of-week surgical scheduling peaks.

This repository deploys **Google TimesFM-3 (Time-Series Foundation Model)** to generate zero-shot, 28-day forward probabilistic bed pressure projections:
* **Context Input:** 60 days of daily CMS census data + Upstate county respiratory viral surveillance (Flu/RSV/COVID).
* **Quantile Outputs:** $P_{10}$ (Optimistic Baseline), $P_{50}$ (Expected Median), and $P_{90}$ (Worst-Case Surge Ceiling).
* **Early Warning Triggers:** Flags capacity crunches **8 to 14 days in advance**, giving clinical bed-placement directors ample lead time to adjust elective surgical schedules.

---

## 🛡️ Medallion Delta Lake Architecture

```
  Federal CMS Datasets & Upstate Viral Feeds (CSV/JSON/API)
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │ 🟫 BRONZE: Raw Ingestion Zone                         │
  │ • Raw provider records dropped off federal stagecoach  │
  │ • Immutable append-only audit ledger                   │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │ ⬜ SILVER: Cleansed Care Coordination Mart              │
  │ • Filtered to SC facilities & keyed by Prisma CCNs     │
  │ • SCD Type 2 tracking with is_tertiary_hub flags      │
  │ • Delta Lake partitioning by facility_id (CCN)         │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │ 🟨 GOLD: Business & Predictive Intelligence            │
  │ • Google TimesFM-3 28-Day Bed Surge Forecasts          │
  │ • Upstate Transfer Optimization & ROI Analytics        │
  │ • Automated GitHub Pages Executive Web Dashboard       │
  └────────────────────────────────────────────────────────┘
```

---

## 🖥️ Omarchy Edge Compute Asset Integration

The **Omarchy Bare-Metal Arch Linux Workstation (`omarchy-node-01` @ `192.168.50.53`)** functions as the high-throughput edge execution asset:
* **Zero-Shot Foundation Inference:** Runs TimesFM-3 model calculations with zero cloud ingress latency.
* **Continuous Test Verification:** Executes the full PyTest suite against Delta Lake partitions directly in bare-metal Python.
* **Live Operations Streaming:** Broadcasts pipeline telemetry and transfer alerts to the Omarchy monitoring HUD.

---

## 🚀 Quickstart & Verification

```bash
# Clone repository
git clone https://github.com/FreeFades2Black/prisma-upstate-care-lakehouse.git
cd prisma-upstate-care-lakehouse

# Run full Medallion pipeline (Bronze -> Silver -> Gold)
python src/processing/delta_lakehouse.py

# Run unit and integration test suite
python -m pytest tests/ -v

# Generate local interactive dashboard
python src/visualization/build_dashboard.py
```

---

## 🎯 How to Pitch This in Greenville Interviews

> *"I didn't build a theoretical tutorial; I built a pipeline targeting Prisma Health's actual operational topology.*
>
> *I mapped **Greenville Memorial (`420078`)** as the central tertiary trauma hub and modeled capacity balancing across **Patewood (`420102`)**, **Greer (`420033`)**, **Hillcrest (`420037`)**, and **Easley (`420015`)**.*
>
> *My **TimesFM-3 foundation inference pipeline** consumes Delta tables partitioned by CMS CCN to project acute-care bed pressure over a 4-week window, providing clinical directors actionable lead time before ICU capacity crunches occur."*
