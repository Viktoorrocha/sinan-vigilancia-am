# Vigilância da Dengue no Amazonas — Pipeline SINAN

Pipeline de dados que transforma as notificações públicas de dengue do SINAN (Ministério da Saúde / DataSUS) em indicadores semanais por município, simulando o trabalho de uma equipe de dados que apoia a vigilância epidemiológica do Amazonas, de 2022 a 2025.

## 1. Contexto de negócio

> Projeto de portfólio construído sobre dados públicos reais. Ele simula o trabalho de uma equipe de dados que apoia a vigilância epidemiológica.

**Cenário.** A vigilância em saúde precisa acompanhar, semana a semana e município a município, quantos casos de dengue foram notificados, quantos foram confirmados, quantos evoluíram para formas graves, quantos foram internados e quantos morreram. O microdado público do SINAN não entrega isso pronto: as colunas vêm todas como texto, as categorias vêm codificadas, a idade vem em um código de unidade e valor, campos vazios vêm como texto em branco, não há número de notificação e o ano do arquivo não é o ano da notificação.

**Objetivo.** Entregar uma camada analítica confiável, em que quem for analisar a dengue no Amazonas não precise repetir a limpeza a cada consulta.

**O que o projeto entrega.**

| | |
|---|---|
| Período | 2022–2025 |
| Notificações processadas | 25.071 |
| Óbitos por dengue | 30 |
| Reconciliação silver ↔ gold | 100% (nenhuma notificação perdida ou criada) |
| Testes de qualidade automáticos | 18 |
| Tabela final | Uma linha por semana epidemiológica e município, com notificações, confirmados, sinais de alarme, graves, internações, óbitos e letalidade |

Exemplo de pergunta que a camada gold responde em uma consulta, os dez municípios com mais óbitos:

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

## 2. Arquitetura

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
| bronze | `brz_sinan_dengue` | Dado bruto, tudo como texto, com arquivo de origem e data de carga |
| silver | `slv_sinan_dengue` | Datas tipadas, categorias decodificadas, idade em anos, chave da notificação e deduplicação |
| gold | `gld_dengue_semana_municipio` | Indicadores por semana epidemiológica e município |

**Stack:** Python · pysus · DuckDB · Parquet · Databricks (Unity Catalog, Delta) · dbt · Apache Airflow · Docker Compose

## 3. Decisões técnicas e trade-offs

**Databricks como warehouse, em vez de banco local.**
O processamento pesado roda no serverless do Databricks e não na máquina de desenvolvimento, que tem 8 GB de RAM. Ganho: o pipeline escala sem mudar o código. Custo: dependência de um serviço gerenciado e nenhuma configuração de cluster para ajustar.

**DuckDB para filtrar antes de subir os dados.**
O arquivo nacional é grande para a memória disponível. O DuckDB lê o Parquet direto do disco e filtra pela UF sem carregá-lo inteiro. Ganho: extração leve e rápida. Custo: uma etapa a mais antes da carga.

**dbt para as transformações.**
Cada camada é um modelo versionado com testes declarativos. Ganho: governança, rastreabilidade e manutenção simples. Custo: uma ferramenta a mais para operar, que se justifica porque os testes de qualidade fazem parte do produto.

**Bronze tudo em texto, tipagem só na silver.**
O bronze preserva o dado exatamente como veio. A conversão para data e número usa funções seguras (`try_cast`, `try_to_date`), que viram nulo quando o valor é inválido. Ganho: a carga nunca quebra por um valor sujo. Custo: um valor inválido vira nulo sem aviso, e por isso os testes cobrem datas, idade e categorias.

**Chave da notificação por hash do registro completo.**
O arquivo público não traz número de notificação. A chave é o hash de todos os campos. Ganho: remove duplicatas exatas e permite testar unicidade. Custo: dois registros genuinamente idênticos seriam contados como um (aqui, 2 casos), e uma notificação reclassificada em uma carga posterior entra como registro novo. O tratamento de atualização com upsert é o próximo passo planejado.

**Ano da notificação, e não o ano do arquivo.**
Um arquivo anual traz registros de anos vizinhos, inclusive de 2026 dentro do arquivo de 2025. Todas as agregações usam a data de notificação. Ganho: indicadores corretos por período. Custo: o número de registros por arquivo não equivale ao número por ano.

**Recorte pela UF notificante (`SG_UF_NOT = AM`).**
É o critério com que a vigilância atribui o caso à unidade que o notificou. Ganho: coerência com a rotina da vigilância. Custo: moradores do Amazonas notificados em outros estados ficam de fora.

**Dois ambientes virtuais no mesmo container.**
`pysus` e `dbt` têm requisitos de pacotes incompatíveis. Ganho: cada ferramenta roda com as versões que precisa. Custo: imagem maior e um caminho de execução específico para cada uma.

**Tabelas recriadas por completo a cada execução.**
Com 25 mil linhas, a recarga completa é simples, barata e livre de inconsistência. Custo: não escala para volumes grandes, e por isso o processamento incremental está no planejamento.

## 4. Qualidade de dados

Os testes rodam a cada `dbt build`:

- Unicidade e não nulidade da chave da notificação
- Valores aceitos para UF, sexo, classificação final, evolução e critério de confirmação
- Coerência cronológica: início dos sintomas não pode ser posterior à notificação
- Faixa de idade plausível (severidade de aviso)
- Grão único no gold (semana + município)
- Consistência das métricas do gold: óbitos, confirmados e internações nunca excedem as notificações, e a letalidade fica entre 0 e 100
- Reconciliação entre silver e gold: os totais batem

Características da fonte que o pipeline respeita: cerca de 7,6% das notificações são inconclusivas, os arquivos públicos não trazem casos descartados e o ano mais recente pode ser preliminar.

## 5. Evolução

| Etapa | Status |
|---|---|
| Extração da fonte oficial (4 anos) | Concluída |
| Camadas bronze, silver e gold | Concluídas |
| Testes de qualidade em todas as camadas | Concluídos |
| DAG do Airflow: extração → carga → `dbt build`, com SLA | Em desenvolvimento |
| Dimensão de municípios (IBGE) via API, para nomes e taxas por habitante | Planejada |
| Processamento incremental com upsert na silver | Planejado |
| Cruzamento com estabelecimentos de saúde pelo CNES | Planejado |
| Dashboard sobre a camada gold | Planejado |

## 6. Como executar

1. Copie `.env.example` para `.env` e preencha o host do Databricks, o HTTP path do SQL warehouse e o token de acesso.
2. `docker compose up -d`
3. Execute a extração, envie os Parquet ao Volume de landing e rode:

```bash
docker exec -it airflow-sinan bash -c \
  "cd /opt/airflow/dbt && /opt/venvs/dbt/bin/dbt build --profiles-dir ."
```

## 7. Estrutura

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

## Fonte dos dados

Ministério da Saúde — SINAN (Sistema de Informação de Agravos de Notificação), via DataSUS. Dados públicos.