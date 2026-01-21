# Dados GeoJSON

Os arquivos GeoJSON desta pasta são muito grandes para o GitHub (>100MB).

## Arquivos necessários:

- `areas_urbanizadas_ibge.geojson` - 153.4 MB (128.459 polígonos)
- `malha_der.geojson` - 364.6 MB (379.742 segmentos)
- `malha_estadual_der.geojson` - 12.0 MB (4.779 segmentos)
- `malha_osm.geojson` - 99.2 MB (7.417 segmentos)
- `municipios_sp.geojson` - 70.5 MB (645 polígonos)
- `regioes_administrativas_sp.geojson` - 13.5 MB (16 regiões)
- `indicadores.json` - Metadados (incluído no repositório)

## Como obter os dados:

1. Execute os scripts Python na raiz do projeto para gerar os arquivos:
   - `converter_camadas_adicionais.py`
   - `converter_malha_unica.py`
   - `converter_poligonos_administrativos.py`

2. Ou baixe os dados processados de: [adicionar link para armazenamento externo]

## Estrutura esperada:

```
app_web/data/
├── areas_urbanizadas_ibge.geojson
├── malha_der.geojson
├── malha_estadual_der.geojson
├── malha_osm.geojson
├── municipios_sp.geojson
├── regioes_administrativas_sp.geojson
└── indicadores.json
```
