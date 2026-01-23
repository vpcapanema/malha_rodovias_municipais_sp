# Dados GeoJSON e JSON

Diretório de dados para a aplicação de visualização da Malha Viária Vicinal do Estado de São Paulo.

## Arquivos de Malha Viária

| Arquivo | Descrição | Extensão |
|---------|-----------|----------|
| `malha_vicinal_estimada_osm.geojson` | Malha vicinal estimada somente OSM (Silvio) | 25.918,58 km |
| `malha_vicinal_estimada_com_der.geojson` | Malha vicinal estimada OSM + DER | 47.666,00 km |
| `malha_estadual_federal_der.geojson` | Malha estadual/federal oficial DER | Referência |

## Arquivos de Indicadores

| Arquivo | Descrição | Formato |
|---------|-----------|---------|
| `municipios_geo_indicadores.geojson` | Geometrias + indicadores por município | GeoJSON |
| `municipios_indicadores.json` | Indicadores por município (sem geometria) | JSON |
| `regioes_geo_indicadores.geojson` | Geometrias + indicadores por RA | GeoJSON |
| `regioes_indicadores.json` | Indicadores por RA (sem geometria) | JSON |

## Arquivos Auxiliares

| Arquivo | Descrição |
|---------|-----------|
| `auxiliar_estatisticas_malha.json` | Estatísticas consolidadas da malha |
| `auxiliar_pavimentacao_malha_total.json` | Dados de pavimentação da malha total |
| `auxiliar_populacao_ibge.json` | População IBGE 2025 por município |

## Diretórios de Tiles

| Diretório | Descrição |
|-----------|-----------|
| `tiles/` | Tiles vetoriais da malha OSM |
| `malha_total_tiles/` | Tiles vetoriais da malha total (OSM + DER) |

## Referências Técnicas

- **CRS**: EPSG:31983 (SIRGAS 2000 / UTM 23S)
- **Municípios**: 645
- **Regiões Administrativas**: 16
- **População IBGE 2025**: 46.081.801 habitantes
