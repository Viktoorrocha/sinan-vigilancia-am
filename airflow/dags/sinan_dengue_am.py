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

CARREGAR_NO_VOLUME = """
set -euo pipefail
DESTINO="/Volumes/sinan_vigilancia/bronze/landing/dengue"
for f in /opt/airflow/extract/dengue/data/deng_am_*.parquet; do
  nome=$(basename "$f")
  echo "Enviando $nome"
  curl -sS --fail -X PUT \
    -H "Authorization: Bearer $DATABRICKS_TOKEN" \
    --data-binary @"$f" \
    "https://$DATABRICKS_HOST/api/2.0/fs/files$DESTINO/$nome?overwrite=true"
done
echo "Carga concluída"
"""

DBT_BUILD = """
set -euo pipefail
cd /opt/airflow/dbt
/opt/venvs/dbt/bin/dbt build --profiles-dir .
"""

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
        bash_command=("/opt/venvs/pysus/bin/python "
                      "/opt/airflow/extract/dengue/extract_sinan_dengue.py"),
    )
    carregar = BashOperator(task_id="carregar_no_volume", bash_command=CARREGAR_NO_VOLUME)
    transformar = BashOperator(task_id="dbt_build", bash_command=DBT_BUILD)

    extrair >> carregar >> transformar
