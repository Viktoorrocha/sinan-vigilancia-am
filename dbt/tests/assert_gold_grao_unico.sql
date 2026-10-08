select ano_epi, semana_epi, cod_municipio, count(*) as qtd
from {{ ref('gld_dengue_semana_municipio') }}
group by 1, 2, 3
having count(*) > 1