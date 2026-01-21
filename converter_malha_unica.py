#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte a ÚNICA malha vicinal autorizada para GeoJSON
Arquivo: Rodovias_municipais_wgsutm23s_intesect_mun.shp
"""

import geopandas as gpd
import json
from pathlib import Path

print("=" * 80)
print("CONVERSÃO DA MALHA VICINAL ÚNICA")
print("=" * 80)

# Caminho do shapefile
shp_path = Path(r"D:\ESTUDO_VICINAIS_V2\motodologia_abordagem_silvio\Vicinais\Avaliacao_OSM_p_Vicinais\Avaliacao_OSM_p_Vicinais\Rodovias Municipais_20250516\Rodovias_municipais_wgsutm23s_intesect_mun.shp")

if not shp_path.exists():
    print(f"❌ ERRO: Arquivo não encontrado!")
    print(f"   Caminho: {shp_path}")
    exit(1)

print(f"\n✓ Arquivo encontrado: {shp_path.name}")

# Ler shapefile
print("\n1. Lendo shapefile...")
gdf = gpd.read_file(shp_path)

print(f"   • {len(gdf):,} features")
print(f"   • CRS: {gdf.crs}")
print(f"   • Tipo: {gdf.geometry.type.unique()}")

# Reprojetar para WGS84 se necessário
if gdf.crs and gdf.crs.to_epsg() != 4326:
    print(f"\n2. Reprojetando {gdf.crs.to_epsg()} → EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)
    print("   ✓ Reprojetado para WGS84")
else:
    print("\n2. Já está em WGS84")

# Verificar colunas
print(f"\n3. Colunas disponíveis:")
for col in gdf.columns:
    if col != 'geometry':
        print(f"   • {col}: {gdf[col].dtype}")

# Calcular comprimento se não existir
if 'comprimento_m' not in gdf.columns:
    print("\n4. Calculando comprimento...")
    # Reprojetar temporariamente para métrico
    gdf_metric = gdf.to_crs(epsg=31983)  # SIRGAS 2000 UTM 23S
    gdf['comprimento_m'] = gdf_metric.geometry.length
    print(f"   ✓ Comprimento calculado")
else:
    print("\n4. Coluna 'comprimento_m' já existe")

# Converter campos Timestamp para string (fix JSON serialization)
print("\n4.1. Convertendo campos datetime...")
for col in gdf.columns:
    if gdf[col].dtype == 'datetime64[ns]' or gdf[col].dtype == 'datetime64[ms]':
        gdf[col] = gdf[col].astype(str)
        print(f"   • {col} → string")

# Estatísticas
extensao_total_km = gdf['comprimento_m'].sum() / 1000
print(f"\n5. Estatísticas:")
print(f"   • Total de segmentos: {len(gdf):,}")
print(f"   • Extensão total: {extensao_total_km:,.1f} km")

# Converter para GeoJSON
print(f"\n6. Convertendo para GeoJSON...")
output_path = Path("app_web/data/malha_osm.geojson")
output_path.parent.mkdir(parents=True, exist_ok=True)

geojson_str = gdf.to_json()
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(geojson_str)

# Tamanho do arquivo
file_size_mb = output_path.stat().st_size / (1024 * 1024)
print(f"   ✓ Salvo: {output_path}")
print(f"   ✓ Tamanho: {file_size_mb:.1f} MB")

# Atualizar indicadores.json
print(f"\n7. Atualizando indicadores...")
indicadores = {
    "osm": {
        "segmentos": len(gdf),
        "extensao_km": int(extensao_total_km)
    },
    "der": {
        "segmentos": 379742,
        "extensao_km": 334001
    }
}

# Tentar ler DER se existir
der_path = Path("dados/vicinais_simples.gpkg")
if der_path.exists():
    try:
        der = gpd.read_file(der_path)
        der_metric = der.to_crs(epsg=31983)
        der_km = der_metric.geometry.length.sum() / 1000
        indicadores["der"] = {
            "segmentos": len(der),
            "extensao_km": int(der_km)
        }
        print(f"   ✓ DER: {len(der):,} segmentos, {der_km:,.1f} km")
    except:
        pass

with open("app_web/data/indicadores.json", 'w', encoding='utf-8') as f:
    json.dump(indicadores, f, indent=2, ensure_ascii=False)

print(f"   ✓ indicadores.json atualizado")

print("\n" + "=" * 80)
print("✓ CONVERSÃO CONCLUÍDA")
print("=" * 80)
print(f"\nArquivo gerado: {output_path}")
print(f"Malha única: {len(gdf):,} segmentos, {extensao_total_km:,.1f} km")
print("\n⚠️  SUBSTITUIU o arquivo anterior malha_osm.geojson")
print("   Agora os mapas usarão APENAS esta malha vicinal")
