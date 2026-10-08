# Vigilância da Dengue no Amazonas — Pipeline SINAN

Pipeline de dados que transforma as notificações públicas de dengue do SINAN (Ministério da Saúde / DataSUS) em tabelas analíticas prontas para uso, com foco no estado do Amazonas, de 2022 a 2025.

O resultado é uma camada analítica que responde, por semana epidemiológica e município: quantos casos foram notificados, quantos confirmados, quantos graves, quantas internações e óbitos, e qual a letalidade.

## Em números

| | |
|---|---|
| Período | 2022–2025 |
| Notificações processadas | 25.071 |
| Óbitos por dengue | 30 |
| Fonte | SINAN — DataSUS (dados públicos oficiais) |
| Testes de qualidade | 16 em execução automática |

## Arquitetura

```
FTP do DataSUS (SINAN DENG)
        │  Python + pysus + DuckDB: filtra UF = AM, grava Parquet
        ▼
Volume do Databricks (landing)
        │
        ▼
bronze  ──►  silver  ──►  gold
        └──────── dbt ────────┘
        Orquestração: Apache Airflow (Docker)
```

| Camada | Modelo | Conteúdo |
|---|---|---|
| bronze | `brz_sinan_dengue` | Dado bruto com rastreabilidade: arquivo de origem e data de carga |
| silver | `slv_sinan_dengue` | Datas tipadas, categorias decodificadas, idade em anos, chave da notificação e deduplicação |
| gold | `gld_dengue_semana_municipio` | Indicadores por semana epidemiológica e município |

Exemplo de consulta sobre a camada gold, os dez municípios com mais óbitos:

```sql
select cod_municipio,
       sum(notificacoes)       as notificacoes,
       sum(casos_confirmados)  as confirmados,
       sum(obitos)             as obitos
from sinan_vigilancia.gold.gld_dengue_semana_municipio
group by cod_municipio
order by obitos desc
limit 10;
```

## Decisões de modelagem

- **Chave da notificação.** O arquivo público não traz número de notificação. A chave é o hash do registro completo, usada para remover duplicatas exatas.
- **Ano da notificação, não do arquivo.** O arquivo de um ano contém registros de anos vizinhos. Todas as agregações usam a data de notificação.
- **Recorte por UF notificante** (`SG_UF_NOT = AM`), o critério usado pela vigilância para atribuir o caso a quem notificou.
- **Campos em branco.** O SINAN grava vazio como string vazia. Eles são convertidos em nulo antes da decodificação, para que "ignorado" seja uma única categoria.
- **Idade.** O código de idade do SINAN (unidade + valor) é convertido para anos.
- **Dependências isoladas.** `pysus` e `dbt` rodam em ambientes virtuais separados dentro do mesmo container, porque seus requisitos de pacotes são incompatíveis.

## Qualidade de dados

Os testes rodam a cada `dbt build`:

- Unicidade e não nulidade da chave da notificação
- Valores aceitos para UF, sexo, classificação final, evolução e critério de confirmação
- Coerência cronológica entre data de sintomas e data de notificação
- Faixa de idade plausível
- Grão único no gold (semana + município)
- Consistência das métricas do gold: óbitos, confirmados e internações nunca excedem as notificações, e a letalidade fica entre 0 e 100
- Reconciliação entre silver e gold: os totais batem

## Stack

Python · pysus · DuckDB · Parquet · Databricks (Unity Catalog, Delta) · dbt · Apache Airflow · Docker Compose

## Estrutura

```
.
├── docker-compose.yml
├── Dockerfile
├── extract/dengue/       # extração (pysus → Parquet)
├── dbt/
│   ├── models/{bronze,silver,gold}/
│   ├── tests/
│   └── macros/
├── airflow/              # DAGs
└── .env.example
```

## Como executar

1. Copie `.env.example` para `.env` e preencha o host do Databricks, o HTTP path do SQL warehouse e o token de acesso.
2. `docker compose up -d`
3. Execute a extração, envie os Parquet ao Volume de landing e rode:

```bash
docker exec -it airflow-sinan bash -c \
  "cd /opt/airflow/dbt && /opt/venvs/dbt/bin/dbt build --profiles-dir ."
```

## Próximos passos

- DAG do Airflow para orquestrar extração, carga e `dbt build`
- Dimensão de municípios (IBGE) com nomes e população, para taxas de incidência
- Cruzamento com estabelecimentos de saúde pelo código CNES
- Processamento incremental com upsert na silver
- Dashboard sobre a camada gold

## Fonte dos dados

Ministério da Saúde — SINAN (Sistema de Informação de Agravos de Notificação), via DataSUS.