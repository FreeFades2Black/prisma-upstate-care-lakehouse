# Multi-stage Dockerfile for Prisma Upstate Regional Care Coordination Lakehouse
# Stage 1: Pipeline Builder & Model Backtester
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt* ./
RUN pip install --no-cache-dir pydantic pytest

# Copy source code and test suite
COPY src/ ./src/
COPY tests/ ./tests/
COPY pytest.ini ./

# Execute full Medallion pipeline (Bronze -> Silver -> Gold) and build executive dashboard
RUN python src/processing/delta_lakehouse.py && \
    python src/visualization/build_dashboard.py && \
    mkdir -p /app/docs && \
    cp -r data/gold/* /app/docs/ || true

# Stage 2: Ultra-Lightweight Production Runtime
FROM python:3.11-alpine AS runtime

WORKDIR /app

# Non-root security user (CIS / HIPAA compliant standard)
RUN addgroup -g 10002 prismacare && \
    adduser -u 10002 -G prismacare -s /bin/sh -D prismacare

# Copy compiled dashboard and gold artifacts from builder
COPY --from=builder --chown=prismacare:prismacare /app/docs /app/docs
COPY --from=builder --chown=prismacare:prismacare /app/data/gold /app/data/gold

USER 10002:10002

EXPOSE 8820

# Serve dashboard on port 8820
CMD ["python", "-m", "http.server", "8820", "--directory", "/app/docs"]
