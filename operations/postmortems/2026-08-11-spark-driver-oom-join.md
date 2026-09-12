# Incident Post-Mortem: PySpark Driver OOM on Broadcast Join of Unpartitioned Geospatial Shapes

**Incident Date:** 2026-08-11  
**Impact Duration:** 32 minutes  
**Severity:** SEV-2  
**Root Cause:** A batch analytics query joined 5 years of unpartitioned hospital census telemetry with high-resolution South Carolina county boundary GeoJSON polygons. The query optimizer attempted an automatic broadcast join (`autoBroadcastJoinThreshold`), exhausting the 4GB driver memory.

## Timeline
* **03:15 UTC:** Daily ICU census rollup job triggered.
* **03:18 UTC:** PySpark driver crashed with `java.lang.OutOfMemoryError: Java heap space`.
* **03:25 UTC:** On-call engineer identified broadcast exchange of 1.2GB uncompressed shapefile data.
* **03:38 UTC:** Disabled broadcast join for geospatial tables; switched to partitioned sort-merge join on `county_fips_code`.
* **03:47 UTC:** Job re-run succeeded in 3.4 minutes.

## Corrective Actions
1. Explicitly set `spark.sql.autoBroadcastJoinThreshold = -1` in geospatial joining modules.
2. Pre-partitioned Bronze hospital records by `census_year` and `county_fips_code`.
