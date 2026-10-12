"""Painel de vigilância da dengue no Amazonas (SINAN, 2022-2025).

Lê o snapshot da camada gold exportado pelo pipeline (app/data/*.parquet).
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ARQUIVO = Path(__file__).parent / "data" / "gld_dengue_semana_municipio.parquet"
ANOS_ANALISE = [2022, 2023, 2024, 2025]
PALETA_ANOS = ["#56B4E9", "#E69F00", "#009E73", "#CC79A7"]
METRICAS = {
    "Notificações": "notificacoes",
    "Casos confirmados": "casos_confirmados",
    "Óbitos": "obitos",
}

st.set_page_config(page_title="Dengue no Amazonas", layout="wide")


@st.cache_data
def carregar() -> pd.DataFrame:
    dados = pd.read_parquet(ARQUIVO)
    return dados[dados["ano_epi"].isin(ANOS_ANALISE)]


def numero_br(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def curva_semanal(dados, base, coluna, anos):
    """Soma por (ano, semana) preenchendo com zero as semanas sem registro."""
    semanal = dados.groupby(["ano_epi", "semana_epi"])[coluna].sum()
    linhas = []
    for ano in anos:
        ultima_semana = int(base.loc[base["ano_epi"] == ano, "semana_epi"].max())
        for semana in range(1, ultima_semana + 1):
            linhas.append((ano, semana, int(semanal.get((ano, semana), 0))))
    return pd.DataFrame(linhas, columns=["ano_epi", "semana_epi", coluna])


base = carregar()

st.title("Dengue no Amazonas")
st.caption(
    "Projeto de portfólio de engenharia de dados, com dados públicos do SINAN/DATASUS "
    "(2022–2025). Não é uma ferramenta oficial de vigilância."
)

with st.sidebar:
    st.header("Filtros")
    anos = st.multiselect("Anos", ANOS_ANALISE, default=ANOS_ANALISE)
    municipios = st.multiselect(
        "Municípios",
        sorted(base["nome_municipio"].dropna().unique()),
        placeholder="Todos",
    )
    rotulo = st.radio("Métrica nos gráficos", list(METRICAS))

coluna = METRICAS[rotulo]
dados = base[base["ano_epi"].isin(anos)]
if municipios:
    dados = dados[dados["nome_municipio"].isin(municipios)]

if dados.empty:
    st.warning("Nenhum dado para os filtros escolhidos.")
    st.stop()

notificacoes = int(dados["notificacoes"].sum())
confirmados = int(dados["casos_confirmados"].sum())
obitos = int(dados["obitos"].sum())
letalidade = obitos * 100 / confirmados if confirmados else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Notificações", numero_br(notificacoes))
c2.metric("Casos confirmados", numero_br(confirmados))
c3.metric("Óbitos", numero_br(obitos))
c4.metric("Letalidade", f"{letalidade:.2f}%".replace(".", ","))

st.subheader(f"{rotulo} por semana epidemiológica")
curva = curva_semanal(dados, base, coluna, sorted(anos))
st.altair_chart(
    alt.Chart(curva)
    .mark_line()
    .encode(
        x=alt.X("semana_epi:Q", title="Semana epidemiológica", scale=alt.Scale(domain=[1, 53])),
        y=alt.Y(f"{coluna}:Q", title=rotulo),
        color=alt.Color(
            "ano_epi:N",
            title="Ano",
            scale=alt.Scale(domain=ANOS_ANALISE, range=PALETA_ANOS),
        ),
        tooltip=[
            alt.Tooltip("ano_epi:N", title="Ano"),
            alt.Tooltip("semana_epi:Q", title="Semana"),
            alt.Tooltip(f"{coluna}:Q", title=rotulo),
        ],
    )
    .properties(height=340, width="container")
)

esquerda, direita = st.columns(2)

with esquerda:
    st.subheader(f"Municípios com mais {rotulo.lower()}")
    top = dados.groupby("nome_municipio", as_index=False)[coluna].sum().nlargest(10, coluna)
    st.altair_chart(
        alt.Chart(top)
        .mark_bar()
        .encode(
            x=alt.X(
                f"{coluna}:Q",
                title=rotulo,
                axis=alt.Axis(labelExpr="replace(format(datum.value, ','), /,/g, '.')"),
            ),
            y=alt.Y("nome_municipio:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("nome_municipio:N", title="Município"),
                alt.Tooltip(f"{coluna}:Q", title=rotulo),
            ],
        )
        .properties(height=340, width="container")
    )

with direita:
    st.subheader("Resumo por ano")
    anual = dados.groupby("ano_epi", as_index=False)[
        ["notificacoes", "casos_confirmados", "obitos"]
    ].sum()
    anual["letalidade_pct"] = (anual["obitos"] * 100 / anual["casos_confirmados"]).round(2)
    anual["ano_epi"] = anual["ano_epi"].astype(str)
    anual.columns = ["Ano", "Notificações", "Confirmados", "Óbitos", "Letalidade (%)"]
    st.dataframe(anual, hide_index=True)
    st.caption(
        "Óbitos dos anos mais recentes podem ainda estar em investigação; "
        "a queda da letalidade deve ser lida com cautela."
    )

with st.expander("Sobre os dados"):
    st.markdown(
        """
- **Fonte:** SINAN (DATASUS), arquivos de dengue de 2022 a 2025, filtrados pela UF de notificação = Amazonas.
- **Município:** o de notificação, com nome vindo da API de localidades do IBGE.
- **Letalidade:** óbitos pelo agravo dividido pelos casos confirmados.
- **2026 fora da análise:** o pipeline ingere os arquivos de 2022 a 2025. O ano epidemiológico de 2026 aparece com apenas 37 notificações (semanas 1 a 19) e não representa o ano.
- **Dado preliminar:** o ano mais recente pode mudar conforme o DATASUS atualiza os arquivos.
- **Cobertura:** 54 dos 62 municípios do estado têm ao menos uma notificação no período.
"""
    )
