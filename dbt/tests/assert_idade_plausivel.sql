{{ config(severity='warn') }}
-- Idade fora de 0 a 120 anos indica erro de digitação na origem.
select chave_notificacao
from {{ ref('slv_sinan_dengue') }}
where idade_anos < 0 or idade_anos > 120
