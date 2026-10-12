-- Camada gold: dengue (AM) agregada por semana epidemiológica e município de notificação.
-- Grão: 1 linha por (ano_epi, semana_epi, município de notificação).
-- Letalidade = óbitos pelo agravo / casos confirmados (null quando não há confirmados).
-- O nome do município vem da referência oficial do IBGE (seed ref_municipios_am).

with agregado as (
    select
        ano_epi_notificacao                                         as ano_epi,
        semana_epi_notificacao                                      as semana_epi,
        cod_municipio_notificacao                                   as cod_municipio,

        count(*)                                                    as notificacoes,
        count_if(is_caso_confirmado)                                as casos_confirmados,
        count_if(cod_classificacao_final = '11')                    as casos_sinais_alarme,
        count_if(cod_classificacao_final = '12')                    as casos_graves,
        count_if(hospitalizado)                                     as hospitalizacoes,
        count_if(is_obito_dengue)                                   as obitos,
        round(try_divide(count_if(is_obito_dengue) * 100.0,
                         count_if(is_caso_confirmado)), 2)          as letalidade_pct
    from {{ ref('slv_sinan_dengue') }}
    where ano_epi_notificacao is not null
      and semana_epi_notificacao between 1 and 53
      and cod_municipio_notificacao is not null
    group by 1, 2, 3
)

select
    a.ano_epi,
    a.semana_epi,
    a.cod_municipio,
    m.nome_municipio,
    a.notificacoes,
    a.casos_confirmados,
    a.casos_sinais_alarme,
    a.casos_graves,
    a.hospitalizacoes,
    a.obitos,
    a.letalidade_pct
from agregado a
left join {{ ref('ref_municipios_am') }} m
    on a.cod_municipio = m.cod_municipio
