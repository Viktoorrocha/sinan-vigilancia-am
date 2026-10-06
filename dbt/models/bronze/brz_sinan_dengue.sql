-- Camada bronze: cópia fiel dos arquivos do SINAN (dengue, AM), sem transformação.
-- Só adiciona colunas de rastreabilidade (arquivo de origem e momento da carga).
select
    *,
    _metadata.file_name as arquivo_origem,
    current_timestamp() as carregado_em
from read_files(
    '/Volumes/sinan_vigilancia/bronze/landing/dengue/',
    format => 'parquet'
)
