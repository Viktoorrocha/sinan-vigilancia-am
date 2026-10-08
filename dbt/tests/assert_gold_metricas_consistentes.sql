select *
from {{ ref('gld_dengue_semana_municipio') }}
where casos_confirmados > notificacoes
   or obitos > notificacoes
   or casos_sinais_alarme + casos_graves > casos_confirmados
   or hospitalizacoes > notificacoes
   or letalidade_pct < 0
   or letalidade_pct > 100