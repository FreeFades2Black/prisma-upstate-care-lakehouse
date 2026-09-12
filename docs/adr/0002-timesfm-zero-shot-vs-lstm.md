# ADR-0002: Google TimesFM Zero-Shot Foundation Model vs Custom LSTM for ICU Bed Surge Forecasting

**Status:** Accepted  
**Date:** 2026-07-04  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
Forecasting ICU bed occupancy surges during seasonal respiratory virus outbreaks requires modeling non-linear, multi-horizon demand curves across regional Prisma Upstate facilities.

## 2. Options Considered
* **Option A: Custom Retrained LSTM / DeepAR Neural Networks**
  - *Evaluation:* Requires constant retraining pipelines, delicate hyperparameter tuning per facility, and suffers from catastrophic forgetting during abrupt distribution shifts (e.g. novel epidemics).
* **Option B: Google TimesFM (Time Series Foundation Model) Zero-Shot Inference**
  - *Evaluation:* Pre-trained on 100B+ time-series points; delivers superior mean absolute percentage error (MAPE) out of the box without local retraining pipelines.

## 3. Decision & Trade-Off Accepted
We adopted **Option B (TimesFM Zero-Shot)**.  
**Trade-Off Accepted:** Inference requires higher CPU/GPU memory footprint during batch prediction runs; mitigated by caching rolling 14-day forecasts into Gold Delta Lake tables.
