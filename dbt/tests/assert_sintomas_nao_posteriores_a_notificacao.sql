{{ config(severity='warn') }}
-- Primeiros sintomas não podem ser depois da notificação.
select chave_notificacao
from {{ ref('slv_sinan_dengue') }}
where data_primeiros_sintomas > data_notificacao
