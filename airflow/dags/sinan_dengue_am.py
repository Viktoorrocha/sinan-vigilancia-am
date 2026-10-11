"""DAG do pipeline SINAN dengue (AM): extração -> carga -> dbt build."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "viktor",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "sla": timedelta(minutes=30),
}

with DAG(
    dag_id="sinan_dengue_am",
    description="Pipeline SINAN dengue (AM): extração, carga e dbt build",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * 1",
    catchup=False,
    default_args=default_args,
    tags=["sinan", "dengue", "saude"],
) as dag:

    extrair = BashOperator(
        task_id="extrair_sinan_dengue",
        bash_command=(
            "/opt/venvs/pysus/bin/python "
            "/opt/airflow/extract/dengue/extract_sinan_dengue.py"
        ),
    )