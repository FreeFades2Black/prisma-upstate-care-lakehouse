# ADR-0001: Delta Lake ACID Merge over Flat Parquet for CMS CCN SCD Type 2 Hospital Dimensions

**Status:** Accepted  
**Date:** 2026-06-15  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
Tracking hospital facility capabilities across the Upstate South Carolina health network requires maintaining slowly changing dimension (SCD Type 2) historical records for each CMS CMS Certification Number (CCN). Updates arrive continuously via telemetry streams.

## 2. Options Considered
* **Option A: Flat Apache Parquet Files on Cloud Object Storage**
  - *Evaluation:* Inexpensive, but lacks atomic row-level updates; any modification to hospital bed counts requires full table rewrites, risking read anomalies during concurrent analytics jobs.
* **Option B: Delta Lake with ACID Transaction Log (`_delta_log`) and MERGE INTO Support**
  - *Evaluation:* Supports atomic upserts (`MERGE INTO silver_hospitals USING updates ON ccn`), automatic file compaction (`OPTIMIZE`), and time-travel querying (`VERSION AS OF`).

## 3. Decision & Trade-Off Accepted
We adopted **Option B (Delta Lake)**.  
**Trade-Off Accepted:** Storage volume expands due to historical file versions prior to `VACUUM` execution; requires 7-day retention management to maintain auditability without excessive cloud storage bloat.
