FROM python:3.12-slim

ARG PREFECT_VERSION=3.8.7

WORKDIR /app

# Prefect 3.8.7's scheduler is incompatible with SQLAlchemy 2.1 hybrid bulk DML.
RUN apt-get update && apt-get install -y cron \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        "prefect==${PREFECT_VERSION}" \
        "fastapi==0.139.0" \
        "dbt-core==1.11.7" \
        "dbt-postgres==1.10.0" \
        "sqlalchemy>=2.0,<2.1" \
        "psycopg[binary]>=3.2" \
        "python-dotenv>=1.0" \
        "beautifulsoup4>=4.13" \
        "dateparser>=1.2" \
        "playwright>=1.51" \
    && rm -rf /var/lib/apt/lists/*

# Le pilote Node de Playwright nécessite libatomic, même avec Browserless distant.
RUN apt-get update && apt-get install -y --no-install-recommends libatomic1 \
    && rm -rf /var/lib/apt/lists/* \
    && python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.stop()"

COPY . /app
COPY ingestion/prefect/cleanup_crontab /etc/cron.d/cleanup_crontab
RUN chmod 0644 /etc/cron.d/cleanup_crontab && crontab /etc/cron.d/cleanup_crontab

ENV PYTHONPATH=/app
ENV DBT_PROFILES_DIR=/app/ingestion/dbt/profiles

WORKDIR /app

CMD service cron start && prefect
