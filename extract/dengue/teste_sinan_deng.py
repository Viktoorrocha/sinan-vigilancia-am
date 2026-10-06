import duckdb
import pysus

ANOS = [2022, 2023, 2024, 2025]

con = duckdb.connect()
resumo = []

for ano in ANOS:
    try:
        bag = pysus.ftp.sinan("DENG", ano, source="origin")
        paths = bag.paths
    except Exception as e:
        print(f"[{ano}] não disponível: {type(e).__name__}: {str(e)[:150]}")
        continue

    for p in paths:
        brasil = con.sql(f"select count(*) from read_parquet('{p}')").fetchone()[0]
        am = con.sql(f"select count(*) from read_parquet('{p}') where SG_UF_NOT = '13'").fetchone()[0]
        ncols = len(con.sql(f"describe select * from read_parquet('{p}')").fetchall())
        destino = f"/opt/airflow/extract/dengue/data/deng_am_{ano}.parquet"
        con.sql(f"copy (select * from read_parquet('{p}') where SG_UF_NOT = '13') to '{destino}' (format parquet)")
        resumo.append((ano, brasil, am, ncols))
        print(f"[{ano}] Brasil: {brasil} | AM: {am} | colunas: {ncols} -> {destino}")

print("\nRESUMO (ano, Brasil, AM, colunas):")
for r in resumo:
    print(r)
