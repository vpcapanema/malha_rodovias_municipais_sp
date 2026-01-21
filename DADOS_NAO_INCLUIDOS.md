# Dados Não Incluídos no Repositório

Devido ao limite de tamanho de arquivo do GitHub (100MB) e políticas de armazenamento, os seguintes arquivos de dados **não estão incluídos** neste repositório:

## Dados Web (app_web/data/)
- `malha_der.geojson` (364.6 MB) - Malha rodoviária DER-SP
- `areas_urbanizadas_ibge.geojson` (153.4 MB) - Áreas urbanizadas IBGE 2019
- `malha_osm.geojson` (99.2 MB) - Malha viária OpenStreetMap
- `municipios_sp.geojson` (70.5 MB) - Municípios de São Paulo
- `malha_estadual_der.geojson` (12.0 MB) - Malha estadual DER-SP
- `regioes_administrativas_sp.geojson` (13.5 MB) - Regiões administrativas

## Dados Processados (dados/)
- `osm_sp_linhas.gpkg` - Linhas viárias OSM processadas
- `vicinais_sp.gpkg` - Malha vicinal completa
- `base_linhas.gpkg` - Base de linhas viárias
- `hierarquia_rotas.gpkg` - Hierarquia de rotas
- `au_ibge.gpkg` - Áreas urbanizadas IBGE
- `malha_municipal_sp.gpkg` - Malha municipal processada
- Diversos arquivos `.shp`, `.dbf`, `.shx` de shapefiles grandes

## Dados Base (dados/Base_OSM/)
- `sudeste-251111_full.gpkg` - GeoPackage completo do Sudeste
- `sudeste-251111.osm.pbf` - Arquivo PBF original OpenStreetMap
- `sudeste_OSM.parquet` - Dados OSM em formato Parquet

## Resultados (resultados/)
- `dados_processados/*.gpkg` - GeoPackages de resultados finais
- `intermediarios/*.gpkg` - GeoPackages de processamento intermediário

## Como Obter os Dados

### Opção 1: Processar do Zero
Execute os scripts Python na ordem:
1. `converter_pbf_gpkg.py` - Converte PBF para GPKG
2. `extrair_malha_municipal.py` - Extrai malha municipal
3. `filtro_area_urbana.py` - Aplica filtros
4. `preparar_dados_mapas.py` - Prepara GeoJSON para web

### Opção 2: Baixar Dados Base
- **OpenStreetMap**: https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf
- **IBGE Áreas Urbanizadas 2019**: https://geoftp.ibge.gov.br/
- **DER-SP Malha Rodoviária**: Disponível em `dados/Sistema Rodoviário Estadual/`

### Opção 3: Contato
Para acesso aos dados processados, entre em contato com o responsável pelo projeto.

## Tamanho Total dos Dados Excluídos
- **Dados Web**: ~713 MB
- **Dados Base OSM**: ~1.5 GB
- **Dados Processados**: ~500 MB
- **Total**: ~2.7 GB

## Nota Importante
O arquivo `.gitignore` foi configurado para excluir automaticamente estes arquivos em futuros commits. Se você clonar este repositório, será necessário regenerar ou baixar os dados seguindo as opções acima.
