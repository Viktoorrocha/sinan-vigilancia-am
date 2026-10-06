FROM apache/airflow:2.10.2-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/venvs && chown -R airflow /opt/venvs

USER airflow

ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

# venv isolado para extração (pysus)
RUN python -m venv /opt/venvs/pysus && \
    /opt/venvs/pysus/bin/pip install --no-cache-dir pysus

# venv isolado para transformação (dbt)
RUN python -m venv /opt/venvs/dbt && \
    /opt/venvs/dbt/bin/pip install --no-cache-dir dbt-core dbt-databricks
