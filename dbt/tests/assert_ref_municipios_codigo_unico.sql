-- A referência precisa ter 1 linha por código; duplicata faria o join multiplicar linhas.
select cod_municipio, count(*) as linhas
from {{ ref('ref_municipios_am') }}
group by 1
having count(*) > 1
