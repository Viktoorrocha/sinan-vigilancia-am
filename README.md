# Vigilância Epidemiológica SINAN — Amazonas

Pipeline de engenharia de dados sobre doenças de notificação compulsória no Amazonas, com dados reais do DataSUS (SINAN). Segundo projeto de portfólio na minha transição de Backend para Engenharia de Dados — foco em cobrir orquestração (Airflow) e transformação com testes (dbt), que não fizeram parte do primeiro case.

## Escopo

- **Doença:** Malária (primeira fase — arquitetura preparada para outros agravos do SINAN, como dengue, em etapas futuras)
- **Geografia:** Amazonas
- **Fonte:** SINAN, extraído via [pysus](https://github.com/AlertaDengue/PySUS) direto do FTP oficial do DataSUS

## Por que esse projeto

O primeiro case (SIH-SUS Oncologia) provou modelagem dimensional e orquestração gerenciada (Databricks Workflows), mas tinha lacunas: extração manual, sem testes de dados automatizados, sem stack open-source de orquestração. Este projeto existe para fechar essas lacunas com Airflow + dbt.

## Arquitetura

```
pysus (extração)
    │
    ▼
Airflow DAG
    ├── task: extrair dados do SINAN
    ├── task: dbt run (transformação)
    └── task: dbt test (qualidade)
    │
    ▼
Warehouse (Postgres local / Databricks)
    │
    ▼
Dashboard / análise
```

## Stack

- **Orquestração:** Apache Airflow (standalone, Docker)
- **Transformação:** dbt
- **Extração:** Python, pysus
- **Storage:** a definir (Postgres local ou Databricks, conforme volume)

## Status

Em construção — fase de estrutura de ambiente.

## Estrutura do repositório

```
├── airflow/           # DAGs, plugins
├── dbt/               # modelos, testes, documentação
├── extract/           # scripts de extração via pysus
├── docs/              # prints e notas de qualidade de dados
└── docker-compose.yml
```

---

Projeto de portfólio — [Viktor Rocha](https://github.com/Viktoorrocha)