"""Baixa os municípios do Amazonas da API de localidades do IBGE e grava o seed do dbt."""
import csv
import gzip
import json
import urllib.request
from pathlib import Path

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/13/municipios"
DESTINO = Path("/opt/airflow/dbt/seeds/ref_municipios_am.csv")
ASSINATURA_GZIP = b"\x1f\x8b"


def main() -> None:
    with urllib.request.urlopen(URL, timeout=60) as resposta:
        conteudo = resposta.read()

    # A API do IBGE pode responder comprimida em gzip mesmo sem pedirmos.
    if conteudo.startswith(ASSINATURA_GZIP):
        conteudo = gzip.decompress(conteudo)
    municipios = json.loads(conteudo.decode("utf-8"))

    # O SINAN usa o código IBGE de 6 dígitos (sem o dígito verificador).
    linhas = sorted((str(m["id"])[:6], m["nome"]) for m in municipios)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["cod_municipio", "nome_municipio"])
        escritor.writerows(linhas)
    print(f"{len(linhas)} municípios gravados em {DESTINO}")


if __name__ == "__main__":
    main()
