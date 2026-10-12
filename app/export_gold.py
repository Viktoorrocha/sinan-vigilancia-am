"""Exporta a camada gold do Databricks para Parquet (consumido pelo app Streamlit)."""
import os
from pathlib import Path

import pyarrow.parquet as pq
from databricks import sql

TABELA = "sinan_vigilancia.gold.gld_dengue_semana_municipio"
DESTINO = Path(__file__).parent / "data" / "gld_dengue_semana_municipio.parquet"


def main() -> None:
    with sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    ) as conexao, conexao.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM {TABELA} ORDER BY ano_epi, semana_epi, cod_municipio"
        )
        tabela = cursor.fetchall_arrow()

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    temporario = DESTINO.with_suffix(".tmp")
    pq.write_table(tabela, temporario, compression="zstd")
    temporario.replace(DESTINO)
    print(f"{tabela.num_rows} linhas exportadas para {DESTINO}")


if __name__ == "__main__":
    main()
