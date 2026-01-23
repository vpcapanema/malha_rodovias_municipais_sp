"""
Script completo para processar MALHA ESTADUAL TOTAL
1. Converte shapefile DER para GeoJSON
2. Une com malha vicinal estimada
3. Calcula indicadores municipais completos
4. Gera todos os arquivos JSON necessários
"""

import geopandas as gpd
import pandas as pd
import json
from pathlib import Path
import numpy as np
from shapely.ops import unary_union

print("=" * 80)
print("PROCESSAMENTO COMPLETO DA MALHA ESTADUAL TOTAL")
print("Malha Vicinal Estimada (OSM) + Malha Oficial DER-SP")
print("=" * 80)
print()

# Caminhos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'docs' / 'data'
SHAPE_DIR = BASE_DIR / 'docs' / 'Sistema Rodoviário Estadual'
RESULTS_DIR = BASE_DIR / 'resultados' / 'dados_processados'

# ============================================================================
# 1. CARREGAR E CONVERTER MALHA DER (SHAPEFILE → GEOJSON)
# ============================================================================
print("[1/7] Carregando e convertendo malha DER...")

der_shp = SHAPE_DIR / 'MALHA_RODOVIARIA.shp'
print(f"  Shapefile: {der_shp}")

der = gpd.read_file(der_shp)
print(f"  ✓ Malha DER carregada: {len(der):,} segmentos")
print(f"  ✓ CRS original: {der.crs}")

# Converter para SIRGAS 2000 / UTM 23S (EPSG:31983)
if der.crs.to_epsg() != 31983:
    print(f"  → Convertendo para EPSG:31983...")
    der = der.to_crs(31983)
    print(f"  ✓ Conversão concluída")

# Calcular extensão DER
extensao_der_km = der.geometry.length.sum() / 1000
print(f"  ✓ Extensão DER: {extensao_der_km:,.2f} km")

# Salvar DER como GeoJSON
der_geojson_path = DATA_DIR / 'malha_der_oficial.geojson'
der.to_file(der_geojson_path, driver='GeoJSON')
print(f"  ✓ GeoJSON salvo: {der_geojson_path}")

# ============================================================================
# 2. CARREGAR MALHA VICINAL ESTIMADA
# ============================================================================
print("\n[2/7] Carregando malha vicinal estimada...")

# Carregar GeoJSON da malha vicinal (por município)
malha_vicinal = gpd.read_file(DATA_DIR / 'municipios_totais.geojson')
print(f"  ✓ Malha vicinal: {len(malha_vicinal)} municípios")

# Carregar segmentos individuais da malha vicinal
malha_osm_segmentos = gpd.read_file(RESULTS_DIR / 'osm_sp_menos_der.gpkg')
print(f"  ✓ Segmentos OSM: {len(malha_osm_segmentos):,}")
print(f"  ✓ CRS OSM: {malha_osm_segmentos.crs}")

# Converter para EPSG:31983 se necessário
if malha_osm_segmentos.crs.to_epsg() != 31983:
    print(f"  → Convertendo OSM para EPSG:31983...")
    malha_osm_segmentos = malha_osm_segmentos.to_crs(31983)
    print(f"  ✓ Conversão concluída")

extensao_vicinal_km = malha_osm_segmentos.geometry.length.sum() / 1000
print(f"  ✓ Extensão vicinal: {extensao_vicinal_km:,.2f} km")

# ============================================================================
# 3. UNIR MALHAS (DER + VICINAL)
# ============================================================================
print("\n[3/7] Unindo malhas DER e Vicinal...")

# Adicionar coluna de origem
der['origem'] = 'DER'
malha_osm_segmentos['origem'] = 'Vicinal'

# Selecionar/padronizar colunas
der_padrao = der[['geometry', 'origem']].copy()
osm_padrao = malha_osm_segmentos[['geometry', 'origem']].copy()

# Concatenar
malha_total = pd.concat([osm_padrao, der_padrao], ignore_index=True)
malha_total = gpd.GeoDataFrame(malha_total, crs=31983)

print(f"  ✓ Malha total: {len(malha_total):,} segmentos")
print(f"    ├─ Vicinal: {len(osm_padrao):,} segmentos")
print(f"    └─ DER:     {len(der_padrao):,} segmentos")

# Calcular extensões
extensao_total_km = malha_total.geometry.length.sum() / 1000
print(f"  ✓ Extensão total: {extensao_total_km:,.2f} km")
print(f"    ├─ Vicinal: {extensao_vicinal_km:,.2f} km ({(extensao_vicinal_km/extensao_total_km)*100:.1f}%)")
print(f"    └─ DER:     {extensao_der_km:,.2f} km ({(extensao_der_km/extensao_total_km)*100:.1f}%)")

# Salvar malha total como GeoJSON
malha_total_path = DATA_DIR / 'malha_vicinal_total_estimada.geojson'
malha_total.to_file(malha_total_path, driver='GeoJSON')
print(f"  ✓ Malha total salva: {malha_total_path}")

# ============================================================================
# 4. CARREGAR DADOS AUXILIARES
# ============================================================================
print("\n[4/7] Carregando dados auxiliares...")

# População
with open(DATA_DIR / 'populacao_ibge.json', 'r', encoding='utf-8') as f:
    pop_ibge = json.load(f)
pop_dict = {str(m['cod_ibge']): m['populacao'] for m in pop_ibge}
print(f"  ✓ População: {len(pop_ibge)} municípios")

# Polígonos municipais
municipios_sp = gpd.read_file(DATA_DIR / 'municipios_sp.geojson')
if municipios_sp.crs.to_epsg() != 31983:
    municipios_sp = municipios_sp.to_crs(31983)
print(f"  ✓ Municípios SP: {len(municipios_sp)} polígonos")

# Indicadores municipais existentes (vicinal)
with open(DATA_DIR / 'municipios_indicadores.json', 'r', encoding='utf-8') as f:
    indicadores_vicinal = json.load(f)
print(f"  ✓ Indicadores vicinal: {len(indicadores_vicinal)} municípios")

# ============================================================================
# 5. CALCULAR EXTENSÃO DA MALHA TOTAL POR MUNICÍPIO
# ============================================================================
print("\n[5/7] Calculando extensão da malha TOTAL por município...")

# Fazer spatial join para saber qual segmento está em qual município
malha_total_com_mun = gpd.sjoin(malha_total, municipios_sp[['CD_MUN', 'NM_MUN', 'geometry']], 
                                 how='left', predicate='intersects')

# Calcular extensão por município
extensoes_municipios = []
for cod_mun in municipios_sp['CD_MUN'].unique():
    segmentos_mun = malha_total_com_mun[malha_total_com_mun['CD_MUN'] == cod_mun]
    
    if len(segmentos_mun) > 0:
        extensao_km = segmentos_mun.geometry.length.sum() / 1000
        extensao_vicinal = segmentos_mun[segmentos_mun['origem'] == 'Vicinal'].geometry.length.sum() / 1000
        extensao_der = segmentos_mun[segmentos_mun['origem'] == 'DER'].geometry.length.sum() / 1000
    else:
        extensao_km = 0
        extensao_vicinal = 0
        extensao_der = 0
    
    extensoes_municipios.append({
        'Cod_ibge': str(cod_mun),
        'extensao_total_km': extensao_km,
        'extensao_vicinal_km': extensao_vicinal,
        'extensao_der_km': extensao_der
    })

df_extensoes = pd.DataFrame(extensoes_municipios)
print(f"  ✓ Extensões calculadas para {len(df_extensoes)} municípios")
print(f"  ✓ Total geral: {df_extensoes['extensao_total_km'].sum():,.2f} km")

# ============================================================================
# 6. CALCULAR INDICADORES COMPLETOS DA MALHA TOTAL
# ============================================================================
print("\n[6/7] Calculando indicadores da malha TOTAL por município...")

# Merge com dados existentes
indicadores_total = []

for idx_vicinal, mun_vicinal in enumerate(indicadores_vicinal):
    cod_ibge = mun_vicinal['Cod_ibge']
    
    # Buscar extensões da malha total
    extensao_row = df_extensoes[df_extensoes['Cod_ibge'] == cod_ibge]
    
    if len(extensao_row) > 0:
        extensao_total = extensao_row.iloc[0]['extensao_total_km']
        extensao_vicinal = extensao_row.iloc[0]['extensao_vicinal_km']
        extensao_der = extensao_row.iloc[0]['extensao_der_km']
    else:
        extensao_total = mun_vicinal['extensao_km']  # fallback
        extensao_vicinal = mun_vicinal['extensao_km']
        extensao_der = 0
    
    # Dados territoriais
    area_km2 = mun_vicinal['Area_Km2']
    pop = pop_dict.get(cod_ibge, mun_vicinal['Pop_2025'])
    
    # Calcular densidades da MALHA TOTAL
    densidade_area_10k = (extensao_total / area_km2) * 10_000
    densidade_area_abs = extensao_total / area_km2
    densidade_pop_10k = (extensao_total / pop) * 10_000 if pop > 0 else 0
    
    # Criar registro
    indicador = {
        'Cod_ibge': cod_ibge,
        'Municipio': mun_vicinal['Municipio'],
        'RA': mun_vicinal['RA'],
        'Area_Km2': round(area_km2, 2),
        'Pop_2025': int(pop),
        # Extensões
        'extensao_total_km': round(extensao_total, 2),
        'extensao_vicinal_km': round(extensao_vicinal, 2),
        'extensao_der_km': round(extensao_der, 2),
        'participacao_vicinal_perc': round((extensao_vicinal / extensao_total * 100) if extensao_total > 0 else 0, 2),
        'participacao_der_perc': round((extensao_der / extensao_total * 100) if extensao_total > 0 else 0, 2),
        # Densidades da malha TOTAL
        'densidade_area_10k': round(densidade_area_10k, 4),
        'densidade_area_abs': round(densidade_area_abs, 6),
        'densidade_pop_10k': round(densidade_pop_10k, 4),
    }
    
    indicadores_total.append(indicador)

print(f"  ✓ Indicadores calculados para {len(indicadores_total)} municípios")

# Calcular estatísticas estaduais
area_total_sp = sum(m['Area_Km2'] for m in indicadores_total)
pop_total_sp = sum(m['Pop_2025'] for m in indicadores_total)
extensao_total_sp = sum(m['extensao_total_km'] for m in indicadores_total)
extensao_vicinal_sp = sum(m['extensao_vicinal_km'] for m in indicadores_total)
extensao_der_sp = sum(m['extensao_der_km'] for m in indicadores_total)

densidade_area_10k_sp = (extensao_total_sp / area_total_sp) * 10_000
densidade_pop_10k_sp = (extensao_total_sp / pop_total_sp) * 10_000

print(f"\n  RESUMO ESTADUAL:")
print(f"  ├─ Extensão total:   {extensao_total_sp:>12,.2f} km")
print(f"  ├─ Extensão vicinal: {extensao_vicinal_sp:>12,.2f} km ({(extensao_vicinal_sp/extensao_total_sp)*100:.1f}%)")
print(f"  ├─ Extensão DER:     {extensao_der_sp:>12,.2f} km ({(extensao_der_sp/extensao_total_sp)*100:.1f}%)")
print(f"  ├─ Densidade área:   {densidade_area_10k_sp:>12,.2f} km/10.000km²")
print(f"  └─ Densidade pop:    {densidade_pop_10k_sp:>12,.2f} km/10.000 hab")

# ============================================================================
# 7. SALVAR RESULTADOS
# ============================================================================
print("\n[7/7] Salvando resultados...")

# Salvar indicadores municipais da malha TOTAL
output_path = DATA_DIR / 'municipios_malha_total.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(indicadores_total, f, ensure_ascii=False, indent=2)
print(f"  ✓ {output_path}")

# Salvar resumo estadual
resumo_estadual = {
    "resumo_geral": {
        "extensao_total_km": round(extensao_total_sp, 2),
        "extensao_vicinal_km": round(extensao_vicinal_sp, 2),
        "extensao_der_km": round(extensao_der_sp, 2),
        "num_segmentos_total": len(malha_total),
        "num_segmentos_vicinal": len(osm_padrao),
        "num_segmentos_der": len(der_padrao),
        "participacao_vicinal_perc": round((extensao_vicinal_sp / extensao_total_sp) * 100, 2),
        "participacao_der_perc": round((extensao_der_sp / extensao_total_sp) * 100, 2)
    },
    "territorio": {
        "area_total_km2": round(area_total_sp, 2),
        "populacao_total": int(pop_total_sp),
        "num_municipios": 645
    },
    "densidades": {
        "densidade_espacial_10k": round(densidade_area_10k_sp, 4),
        "densidade_espacial_abs": round(extensao_total_sp / area_total_sp, 6),
        "densidade_populacional_10k": round(densidade_pop_10k_sp, 4)
    }
}

output_path = DATA_DIR / 'malha_estadual_total.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(resumo_estadual, f, ensure_ascii=False, indent=2)
print(f"  ✓ {output_path}")

print("\n" + "=" * 80)
print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
print("=" * 80)
print(f"\n📊 MALHA ESTADUAL TOTAL: {extensao_total_sp:,.2f} km")
print(f"   ├─ Malha Vicinal (OSM): {extensao_vicinal_sp:,.2f} km ({(extensao_vicinal_sp/extensao_total_sp)*100:.1f}%)")
print(f"   └─ Malha DER (oficial): {extensao_der_sp:,.2f} km ({(extensao_der_sp/extensao_total_sp)*100:.1f}%)")
print(f"\n🔢 SEGMENTOS: {len(malha_total):,} total")
print(f"   ├─ Vicinal: {len(osm_padrao):,}")
print(f"   └─ DER:     {len(der_padrao):,}")
print(f"\n📁 ARQUIVOS GERADOS:")
print(f"   ✓ malha_der_oficial.geojson")
print(f"   ✓ malha_vicinal_total_estimada.geojson")
print(f"   ✓ municipios_malha_total.json")
print(f"   ✓ malha_estadual_total.json")
print("\n" + "=" * 80)
