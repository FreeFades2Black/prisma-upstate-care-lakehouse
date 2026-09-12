## Prisma Lakehouse Operational Overview
*Describe modifications to Medallion pipelines, TimesFM forecasting, or CMS data schemas.*

- [ ] Bronze / Silver / Gold Delta Lake Pipeline
- [ ] TimesFM Forecasting Model & Backtest
- [ ] Inter-Facility Transfer Optimization Engine
- [ ] CMS Hospital Quality & Capacity Schema

## Data Quality & Performance Verification
- **Schema Backward Compatibility:** Confirmed no breaking changes to existing Delta tables.
- **Backtest Validation:** Verified TimesFM forecast MAPE remains below 8.0%.

## Verification Checklist
- [ ] Full pipeline test suite passing (6/6 tests): `python -m pytest tests/ -v`
- [ ] Data files restored and clean
