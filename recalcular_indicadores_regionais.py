# -*- coding: utf-8 -*-
"""
Recalcula indicadores regionais usando as malhas corretas:
- malha_vicinais.geojson (OSM Silvio): 25.918,58 km
- malha_total_estadual.geojson (OSM + DER): 47.666,00 km

Os indicadores são agregados por Região Administrativa (RA).
"""

import json
from pathlib import Path
from collections import defaultdict
import geopandas as gpd

DATA_DIR = Path("docs/data")

print("=" * 70)
print("RECALCULANDO INDICADORES REGIONAIS")
print("=" * 70)

# ============================================================================
# 1. CARREGAR MALHAS
# ============================================================================
print("\n[1/4] Carregando malhas...")

# Malha OSM (Silvio)
osm_gdf = gpd.read_file(DATA_DIR / "malha_vicinais.geojson")
osm_gdf = osm_gdf.to_crs(31983)
osm_gdf['length_km'] = osm_gdf.geometry.length / 1000
osm_total_km = osm_gdf.geometry.length.sum() / 1000
print(f"  ✓ OSM Silvio: {osm_total_km:.2f} km ({len(osm_gdf)} segmentos)")

# Malha Total (OSM + DER)
total_gdf = gpd.read_file(DATA_DIR / "malha_total_estadual.geojson")
total_gdf = total_gdf.to_crs(31983)
total_gdf['length_km'] = total_gdf.geometry.length / 1000
total_total_km = total_gdf.geometry.length.sum() / 1000
print(f"  ✓ Total (OSM+DER): {total_total_km:.2f} km ({len(total_gdf)} segmentos)")

# ============================================================================
# 2. CARREGAR MUNICÍPIOS E RAs
# ============================================================================
print("\n[2/4] Carregando municípios e RAs...")

# Carregar dados complementares (área, população, municípios)
with open(DATA_DIR / "municipios_indicadores.json", "r", encoding="utf-8") as f:
    municipios = json.load(f)

# Criar mapa cod_ibge -> RA
mun_ra_map = {}
for mun in municipios:
    cod = str(mun.get('Cod_ibge', ''))
    ra = mun.get('RA', '')
    mun_ra_map[cod] = ra

# Agregar dados por RA
dados_ra = defaultdict(lambda: {'num_municipios': 0, 'area_km2': 0, 'populacao': 0})
for mun in municipios:
    ra = mun.get('RA', '')
    dados_ra[ra]['num_municipios'] += 1
    dados_ra[ra]['area_km2'] += mun.get('Area_Km2', 0)
    dados_ra[ra]['populacao'] += mun.get('Pop_2025', 0)

print(f"  ✓ {len(municipios)} municípios carregados")
print(f"  ✓ {len(dados_ra)} RAs identificadas")

# Carregar GeoJSON de municípios para spatial join
municipios_gdf = gpd.read_file(DATA_DIR / "municipios_sp.geojson")
municipios_gdf = municipios_gdf.to_crs(31983)
municipios_gdf['Cod_ibge'] = municipios_gdf['Cod_ibge'].astype(str)
# Adicionar RA ao GeoDataFrame de municípios
municipios_gdf['RA'] = municipios_gdf['Cod_ibge'].map(mun_ra_map)
print(f"  ✓ GeoJSON de municípios carregado ({len(municipios_gdf)} polígonos)")

# ============================================================================
# 3. CALCULAR EXTENSÃO POR RA (SPATIAL JOIN VIA MUNICÍPIO)
# ============================================================================
print("\n[3/4] Calculando extensão por RA (via município)...")

# Pegar ponto médio de cada segmento para join
osm_points = osm_gdf.copy()
osm_points['geometry'] = osm_points.geometry.interpolate(0.5, normalized=True)

total_points = total_gdf.copy()
total_points['geometry'] = total_points.geometry.interpolate(0.5, normalized=True)

# Spatial join com MUNICÍPIOS (que têm a RA correta)
osm_mun = gpd.sjoin(osm_points, municipios_gdf[['Cod_ibge', 'RA', 'geometry']], how='left', predicate='within')
total_mun = gpd.sjoin(total_points, municipios_gdf[['Cod_ibge', 'RA', 'geometry']], how='left', predicate='within')

# Agregar por RA
osm_por_ra = osm_mun.groupby('RA')['length_km'].sum().to_dict()
total_por_ra = total_mun.groupby('RA')['length_km'].sum().to_dict()

osm_alocado = sum(osm_por_ra.values())
total_alocado = sum(total_por_ra.values())

print(f"  ✓ OSM alocado: {osm_alocado:.2f} km em {len(osm_por_ra)} RAs")
print(f"  ✓ Total alocado: {total_alocado:.2f} km em {len(total_por_ra)} RAs")

# ============================================================================
# 4. MONTAR INDICADORES POR RA
# ============================================================================
print("\n[4/4] Montando indicadores por RA...")

regioes_result = []

for ra, info in dados_ra.items():
    ext_osm = osm_por_ra.get(ra, 0)
    ext_total = total_por_ra.get(ra, 0)
    area = info['area_km2']
    pop = info['populacao']
    num_mun = info['num_municipios']
    
    # Densidades OSM
    dens_osm_area_10k = (ext_osm / area * 10000) if area > 0 else 0
    dens_osm_pop_10k = (ext_osm / pop * 10000) if pop > 0 else 0
    
    # Densidades Total
    dens_total_area_10k = (ext_total / area * 10000) if area > 0 else 0
    dens_total_area_abs = (ext_total / area) if area > 0 else 0
    dens_total_pop_10k = (ext_total / pop * 10000) if pop > 0 else 0
    
    # Médias por município
    ext_osm_media = ext_osm / num_mun if num_mun > 0 else 0
    ext_total_media = ext_total / num_mun if num_mun > 0 else 0
    
    regioes_result.append({
        'RA': ra,
        'num_municipios': num_mun,
        'area_km2': round(area, 2),
        'populacao': pop,
        'extensao_osm_km': round(ext_osm, 2),
        'extensao_total_km': round(ext_total, 2),
        'densidade_osm_area_10k': round(dens_osm_area_10k, 4),
        'densidade_osm_pop_10k': round(dens_osm_pop_10k, 4),
        'densidade_total_area_10k': round(dens_total_area_10k, 4),
        'densidade_total_area_abs': round(dens_total_area_abs, 6),
        'densidade_total_pop_10k': round(dens_total_pop_10k, 4),
        'extensao_osm_media_mun': round(ext_osm_media, 2),
        'extensao_total_media_mun': round(ext_total_media, 2)
    })

# Calcular desvios (baseado na média das RAs)
media_dens_total_area = sum(r['densidade_total_area_10k'] for r in regioes_result) / len(regioes_result)
media_dens_total_pop = sum(r['densidade_total_pop_10k'] for r in regioes_result) / len(regioes_result)

for r in regioes_result:
    r['desvio_total_dens_area'] = round(
        ((r['densidade_total_area_10k'] - media_dens_total_area) / media_dens_total_area * 100) 
        if media_dens_total_area > 0 else 0, 2
    )
    r['desvio_total_dens_pop'] = round(
        ((r['densidade_total_pop_10k'] - media_dens_total_pop) / media_dens_total_pop * 100)
        if media_dens_total_pop > 0 else 0, 2
    )

# Ordenar por extensão total
regioes_result.sort(key=lambda x: x['extensao_total_km'], reverse=True)

# ============================================================================
# 5. SALVAR RESULTADOS
# ============================================================================
print("\n[5/5] Salvando resultados...")

output = DATA_DIR / 'regioes_indicadores_total.json'
with open(output, 'w', encoding='utf-8') as f:
    json.dump(regioes_result, f, ensure_ascii=False, indent=2)
print(f"  ✓ Salvo: {output}")

# ============================================================================
# RESUMO
# ============================================================================
total_osm_final = sum(r['extensao_osm_km'] for r in regioes_result)
total_geral_final = sum(r['extensao_total_km'] for r in regioes_result)
total_pop = sum(r['populacao'] for r in regioes_result)
total_mun = sum(r['num_municipios'] for r in regioes_result)

print("\n" + "=" * 70)
print("✅ INDICADORES REGIONAIS RECALCULADOS")
print("=" * 70)
print(f"\n📊 TOTAIS:")
print(f"   Extensão OSM Silvio:   {total_osm_final:,.2f} km (esperado: {osm_total_km:,.2f} km)")
print(f"   Extensão TOTAL (OSM+DER): {total_geral_final:,.2f} km (esperado: {total_total_km:,.2f} km)")
print(f"   População:             {total_pop:,}")
print(f"   Municípios:            {total_mun}")
print(f"   Regiões Admin.:        {len(regioes_result)}")

print("\n📋 TOP 5 RAs POR EXTENSÃO TOTAL:")
for i, r in enumerate(regioes_result[:5], 1):
    print(f"   {i}. {r['RA']}: {r['extensao_total_km']:,.1f} km ({r['num_municipios']} mun)")

print("\n📋 DETALHES POR RA:")
print(f"   {'RA':<25} {'OSM (km)':>12} {'Total (km)':>12} {'Pop':>12} {'Mun':>6}")
print("   " + "-" * 70)
for r in regioes_result:
    print(f"   {r['RA']:<25} {r['extensao_osm_km']:>12,.2f} {r['extensao_total_km']:>12,.2f} {r['populacao']:>12,} {r['num_municipios']:>6}")
