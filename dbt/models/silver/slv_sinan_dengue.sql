-- Camada silver: dengue/SINAN (AM) tipada, decodificada e sem duplicatas exatas.
-- Não há número de notificação no arquivo; a chave é um hash da linha inteira.

with sem_metadados as (
    select * except (carregado_em, _rescued_data)
    from {{ ref('brz_sinan_dengue') }}
),

com_chave as (
    select md5(to_json(struct(*))) as chave_notificacao, *
    from sem_metadados
),

deduplicado as (
    select * from com_chave
    qualify row_number() over (partition by chave_notificacao order by chave_notificacao) = 1
),

tratado as (
    select
        chave_notificacao,

        -- períodos
        try_cast(NU_ANO as int)                                     as ano_notificacao,
        try_to_date(nullif(trim(DT_NOTIFIC), ''), 'yyyyMMdd')       as data_notificacao,
        try_to_date(nullif(trim(DT_SIN_PRI), ''), 'yyyyMMdd')       as data_primeiros_sintomas,
        try_to_date(nullif(trim(DT_INVEST), ''), 'yyyyMMdd')        as data_investigacao,
        try_to_date(nullif(trim(DT_INTERNA), ''), 'yyyyMMdd')       as data_internacao,
        try_to_date(nullif(trim(DT_OBITO), ''), 'yyyyMMdd')         as data_obito,
        try_to_date(nullif(trim(DT_ENCERRA), ''), 'yyyyMMdd')       as data_encerramento,
        try_to_date(nullif(trim(DT_DIGITA), ''), 'yyyyMMdd')        as data_digitacao,
        try_cast(left(SEM_NOT, 4) as int)                           as ano_epi_notificacao,
        try_cast(right(SEM_NOT, 2) as int)                          as semana_epi_notificacao,

        -- local
        nullif(trim(SG_UF_NOT), '')                                 as uf_notificacao,
        nullif(trim(ID_MUNICIP), '')                                as cod_municipio_notificacao,
        nullif(trim(SG_UF), '')                                     as uf_residencia,
        nullif(trim(ID_MN_RESI), '')                                as cod_municipio_residencia,
        nullif(trim(ID_UNIDADE), '')                                as cnes_unidade_notificadora,

        -- paciente
        case left(NU_IDADE_N, 1)
            when '4' then try_cast(substr(NU_IDADE_N, 2) as int)
            when '3' then cast(floor(try_cast(substr(NU_IDADE_N, 2) as int) / 12) as int)
            when '2' then 0
            when '1' then 0
        end                                                         as idade_anos,
        case upper(trim(CS_SEXO))
            when 'M' then 'Masculino'
            when 'F' then 'Feminino'
            else 'Ignorado'
        end                                                         as sexo,
        case trim(CS_RACA)
            when '1' then 'Branca'
            when '2' then 'Preta'
            when '3' then 'Amarela'
            when '4' then 'Parda'
            when '5' then 'Indígena'
            else 'Ignorado'
        end                                                         as raca_cor,

        -- classificação e desfecho
        nullif(trim(CLASSI_FIN), '')                                as cod_classificacao_final,

        case trim(CLASSI_FIN)
            when '5'  then 'Descartado'
            when '8'  then 'Inconclusivo'
            when '10' then 'Dengue'
            when '11' then 'Dengue com sinais de alarme'
            when '12' then 'Dengue grave'
            when '13' then 'Chikungunya'
            else 'Não informado'
        end                                                         as classificacao_final,
        case trim(CRITERIO)
            when '1' then 'Laboratorial'
            when '2' then 'Clínico-epidemiológico'
            when '3' then 'Em investigação'
            else 'Não informado'
        end                                                         as criterio_confirmacao,
        nullif(trim(EVOLUCAO), '')                                  as cod_evolucao,
        case trim(EVOLUCAO)
            when '1' then 'Cura'
            when '2' then 'Óbito pelo agravo'
            when '3' then 'Óbito por outra causa'
            when '4' then 'Óbito em investigação'
            else 'Ignorado'
        end                                                         as evolucao,
        case trim(HOSPITALIZ) when '1' then true when '2' then false end as hospitalizado,
        trim(CLASSI_FIN) in ('10', '11', '12')                      as is_caso_confirmado,
        trim(EVOLUCAO) = '2'                                        as is_obito_dengue,

        -- rastreabilidade
        arquivo_origem,
        current_timestamp()                                         as processado_em
    from deduplicado
)

select * from tratado
