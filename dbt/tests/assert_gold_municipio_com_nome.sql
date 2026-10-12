-- Todo município presente na gold precisa ter nome na referência do IBGE.
select distinct cod_municipio
from {{ ref('gld_dengue_semana_municipio') }}
where nome_municipio is null
