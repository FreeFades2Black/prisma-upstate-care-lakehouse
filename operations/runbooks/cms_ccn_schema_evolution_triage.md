# Operational Runbook: CMS CCN Ingestion Schema Evolution & Drift Triage

**Severity:** P2 / Ingestion Pipeline Stalled  
**Target Systems:** Bronze Telemetry Ingestion, Delta Lake Schema Enforcer

## Diagnostic Workflow

### 1. Check Bronze Ingestion Logs for Schema Mismatch
```bash
python -m src.pipeline --check-schema-drift
```
If error contains `AnalysisException: A schema mismatch detected when writing to Delta table`:

### 2. Inspect Inbound Telemetry Payload Changes
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/cms_raw/upstate_cms_hospital_telemetry.csv')
print(df.dtypes)
"
```

### 3. Step-by-Step Remediation
1. If new telemetry columns represent authorized CMS reporting expansions, enable schema evolution:
   ```python
   # Run delta write with mergeSchema option
   df.write.format("delta").mode("append").option("mergeSchema", "true").save(silver_path)
   ```
2. Re-run verification suite:
   ```bash
   python -m pytest tests/test_prisma_lakehouse.py -v
   ```
