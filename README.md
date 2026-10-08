# Pipeline de Vigilância SINAN — Amazonas

Pipeline de dados ponta a ponta construído com **dados públicos reais de vigilância em saúde** (SINAN / DataSUS): notificações de dengue no estado do Amazonas, 2022–2025.

Os dados são extraídos direto da fonte oficial do DataSUS, carregados em um lakehouse Databricks e transformados com dbt em uma arquitetura medalhão (bronze → silver → gold), com testes automatizados de qualidade em todas as camadas.

> Sem dados sintéticos. Todos os números deste projeto vêm da fonte oficial.

## Arquitetura

```
FTP do DataSUS (SINAN DENG)
        │  pysus + DuckDB: filtra UF = AM, grava Parquet
        ▼
Volume do Databricks (landing)
        │  read_files
        ▼
bronze  ──►  silver  ──►  gold
 bruto +      tipado,       casos semanais
 origem       decodificado, por município
              sem           (semana epidemiológica)
              duplicatas
        └──────── modelos e testes dbt ────────┘
```

| Camada | Modelo | O que faz |
|---|---|---|
| bronze | `brz_sinan_dengue` | Parquet bruto, como veio, com nome do arquivo de origem e data de carga |
| silver | `slv_sinan_dengue` | Datas tipadas, categorias decodificadas (sexo, raça/cor, classificação, evolução), idade normalizada em anos, chave substituta e remoção de duplicatas exatas |
| gold | `gld_dengue_semana_municipio` | Notificações, casos confirmados, casos com sinais de alarme, casos graves, hospitalizações, óbitos e letalidade por semana epidemiológica e município |

## Stack

- **Extração:** Python, [pysus](https://github.com/AlertaDengue/PySUS), DuckDB, Parquet
- **Data warehouse:** Databricks (Unity Catalog, Delta, SQL warehouse serverless)
- **Transformação e testes:** dbt (dbt-databricks)
- **Orquestração:** Apache Airflow (Docker)
- **Infraestrutura:** Docker Compose, com dependências isoladas em dois ambientes virtuais (pysus e dbt têm requisitos conflitantes)

## Qualidade de dados

Os testes rodam com `dbt build` (testes genéricos e singulares nas três camadas), incluindo:

- Unicidade e não nulidade da chave da notificação
- Valores aceitos para UF, sexo, classificação final, evolução e critério de confirmação
- Coerência cronológica: início dos sintomas não pode ser posterior à notificação
- Faixa de idade plausível (severidade de aviso)
- Unicidade do grão do gold e consistência das métricas (por exemplo, óbitos ≤ notificações, letalidade entre 0 e 100)
- Reconciliação: os totais de silver e gold batem linha a linha (25.071 notificações, 30 óbitos)

### O que descobri sobre a fonte

Pontos que vale conhecer antes de usar estes arquivos, descobertos durante a construção:

- **O arquivo público de dengue do SINAN não traz o número da notificação**, então não há chave natural. A chave da silver é um hash do registro completo, e apenas 2 duplicatas exatas foram removidas.
- **Ano do arquivo ≠ ano da notificação.** O arquivo de 2025 contém registros notificados em 2026 e alguns de anos anteriores. O pipeline usa o ano da notificação, nunca o ano do arquivo.
- **Filtra-se apenas a UF notificante** (`SG_UF_NOT = AM`). Residentes do Amazonas notificados em outros estados não entram.
- **Campos em branco vêm como string vazia, não como nulo.** Eles são normalizados para nulo antes da decodificação, para não gerar categorias "ignorado" duplicadas.
- **Casos inconclusivos** (classificação 8) somam cerca de 7,6% dos registros. Os arquivos públicos não contêm casos descartados.
- O ano mais recente ainda pode ser preliminar.

## Estrutura do projeto

```
.
├── docker-compose.yml        # container do Airflow
├── Dockerfile                # imagem do Airflow + venvs isolados (pysus e dbt)
├── extract/dengue/           # script de extração (pysus → Parquet)
├── dbt/
│   ├── models/{bronze,silver,gold}/
│   ├── tests/                # testes de dados singulares
│   └── macros/               # sobrescrita da nomenclatura de schemas
├── .env.example              # variáveis de ambiente necessárias
└── airflow/                  # DAGs, logs, plugins
```

## Como rodar

1. Copie `.env.example` para `.env` e preencha o host do Databricks, o HTTP path do SQL warehouse e o token de acesso pessoal.
2. `docker compose up -d`
3. Rode a extração, suba os arquivos Parquet para o Volume de landing e então:

```bash
docker exec -it airflow-sinan bash -c \
  "cd /opt/airflow/dbt && /opt/venvs/dbt/bin/dbt build --profiles-dir ."
```

## Status

- [x] Extração da fonte oficial (4 anos)
- [x] Modelos bronze, silver e gold
- [x] Testes de qualidade em todas as camadas
- [ ] DAG do Airflow orquestrando extração → carga → `dbt build`
- [ ] Dimensão de municípios (IBGE) e cruzamento com estabelecimentos do CNES
- [ ] Processamento incremental e upsert (estilo CDC) na silver
- [ ] Dashboard sobre a camada gold

## Fonte dos dados

Ministério da Saúde — SINAN (Sistema de Informação de Agravos de Notificação), distribuído pelo DataSUS. Dados públicos.