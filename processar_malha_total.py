"""
Script completo para processar MALHA TOTAL ESTADUAL
1. Carrega shapefile DER (EPSG:5880) e converte para EPSG:31983
2. Carrega malha vicinal OSM
3. Une as duas malhas
4. Calcula indicadores por município
5. Gera GeoJSONs finais
"""

import geopandas as gpd
import pandas as pd
import json
from pathlib import Path
from shapely.ops import unary_union
import numpy as np

print("=" * 80)
print("PROCESSAMENTO DA MALHA TOTAL ESTADUAL")
print("Malha Vicinal OSM + Malha Oficial DER")
print("=" * 80)
print()

# Caminhos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'docs' / 'data'
DER_DIR = BASE_DIR / 'docs' / 'Sistema Rodoviário Estadual'

# CRS padrão do projeto
CRS_PADRAO = 31983  # SIRGAS 2000 / UTM 23S

# ============================================================================
# 1. CARREGAR E CONVERTER MALHA DER
# ============================================================================
print("[1/7] Carregando shapefile DER...")
malha_der_shp = DER_DIR / 'MALHA_RODOVIARIA.shp'

der = gpd.read_file(malha_der_shp)
print(f"  ✓ Carregado: {len(der):,} segmentos")
print(f"  CRS original: {der.crs}")

# Converter para EPSG:31983
print(f"\n  Convertendo para EPSG:{CRS_PADRAO} (SIRGAS 2000 / UTM 23S)...")
der_utm = der.to_crs(CRS_PADRAO)
print(f"  ✓ Conversão concluída")

# Calcular extensão DER
extensao_der_km = der_utm.geometry.length.sum() / 1000
print(f"  ✓ Extensão total DER: {extensao_der_km:,.2f} km")

# Salvar GeoJSON do DER
print(f"\n  Salvando malha_der.geojson...")
output_der = DATA_DIR / 'malha_der.geojson'
der_utm.to_file(output_der, driver='GeoJSON')
print(f"  ✓ Salvo: {output_der}")

# ============================================================================
# 2. CARREGAR MALHA VICINAL ESTIMADA
# ============================================================================
print("\n[2/7] Carregando malha vicinal estimada...")

malha_vicinais = DATA_DIR / 'malha_vicinais.geojson'

if not malha_vicinais.exists():
    print(f"  ✗ ERRO: Arquivo não encontrado: {malha_vicinais}")
    exit(1)

osm = gpd.read_file(malha_vicinais)
print(f"  ✓ Carregado de: {malha_vicinais}")
print(f"  ✓ Carregado: {len(osm):,} segmentos")
print(f"  CRS: {osm.crs}")

# Garantir mesmo CRS
if osm.crs.to_epsg() != CRS_PADRAO:
    print(f"  Convertendo OSM para EPSG:{CRS_PADRAO}...")
    osm = osm.to_crs(CRS_PADRAO)
    print(f"  ✓ Conversão concluída")

extensao_osm_km = osm.geometry.length.sum() / 1000
print(f"  ✓ Extensão OSM vicinal: {extensao_osm_km:,.2f} km")

# ============================================================================
# 3. UNIR MALHAS (OSM + DER)
# ============================================================================
print("\n[3/7] Unindo malhas (OSM + DER)...")

# Adicionar coluna de origem
osm['origem'] = 'OSM_Vicinal'
der_utm['origem'] = 'DER_Oficial'

# Padronizar colunas essenciais
osm_sel = osm[['geometry', 'origem']].copy()
der_sel = der_utm[['geometry', 'origem']].copy()

# Concatenar
malha_total = pd.concat([osm_sel, der_sel], ignore_index=True)
malha_total = gpd.GeoDataFrame(malha_total, crs=CRS_PADRAO)

extensao_total_km = malha_total.geometry.length.sum() / 1000

print(f"  ✓ Malha total criada:")
print(f"    - OSM Vicinal:  {len(osm):>8,} segmentos ({extensao_osm_km:>10,.2f} km)")
print(f"    - DER Oficial:  {len(der_utm):>8,} segmentos ({extensao_der_km:>10,.2f} km)")
print(f"    - TOTAL:        {len(malha_total):>8,} segmentos ({extensao_total_km:>10,.2f} km)")

# Salvar GeoJSON da malha total
print(f"\n  Salvando malha_total_estadual.geojson...")
output_total = DATA_DIR / 'malha_total_estadual.geojson'
malha_total.to_file(output_total, driver='GeoJSON')
print(f"  ✓ Salvo: {output_total}")

# ============================================================================
# 4. CARREGAR MUNICÍPIOS
# ============================================================================
print("\n[4/7] Carregando limites municipais...")
municipios = gpd.read_file(DATA_DIR / 'municipios_sp.geojson')

if municipios.crs.to_epsg() != CRS_PADRAO:
    print(f"  Convertendo municípios para EPSG:{CRS_PADRAO}...")
    municipios = municipios.to_crs(CRS_PADRAO)

print(f"  ✓ Carregado: {len(municipios)} municípios")

# ============================================================================
# 5. CALCULAR EXTENSÃO POR MUNICÍPIO (MALHA TOTAL)
# ============================================================================
print("\n[5/7] Calculando extensão por município (malha total)...")

# Fazer interseção espacial
malha_mun_total = gpd.sjoin(malha_total, municipios[['geometry', 'Cod_ibge', 'Municipio']], 
                              how='left', predicate='intersects')

# Calcular extensão por município
extensoes_total = []
for cod_mun in municipios['Cod_ibge'].unique():
    segmentos_mun = malha_mun_total[malha_mun_total['Cod_ibge'] == cod_mun]
    
    if len(segmentos_mun) > 0:
        ext_km = segmentos_mun.geometry.length.sum() / 1000
        extensoes_total.append({
            'Cod_ibge': str(cod_mun),
            'extensao_total_km': round(ext_km, 2)
        })

df_ext_total = pd.DataFrame(extensoes_total)
print(f"  ✓ Extensão calculada para {len(df_ext_total)} municípios")

# ============================================================================
# 6. ATUALIZAR INDICADORES MUNICIPAIS
# ============================================================================
print("\n[6/7] Atualizando indicadores municipais...")

# Carregar indicadores existentes
with open(DATA_DIR / 'municipios_indicadores.json', 'r', encoding='utf-8') as f:
    indicadores_mun = json.load(f)

# Criar DataFrame
df_indicadores = pd.DataFrame(indicadores_mun)

# Merge com extensão total
df_indicadores = df_indicadores.merge(df_ext_total, on='Cod_ibge', how='left')
df_indicadores['extensao_total_km'] = df_indicadores['extensao_total_km'].fillna(0)

# Calcular novos indicadores com malha total
df_indicadores['densidade_total_area_10k'] = (
    df_indicadores['extensao_total_km'] / df_indicadores['Area_Km2']
) * 10_000

df_indicadores['densidade_total_pop_10k'] = (
    df_indicadores['extensao_total_km'] / df_indicadores['Pop_2025']
) * 10_000

# Converter para JSON
indicadores_atualizados = df_indicadores.to_dict('records')

# Salvar
output_ind = DATA_DIR / 'municipios_indicadores_total.json'
with open(output_ind, 'w', encoding='utf-8') as f:
    json.dump(indicadores_atualizados, f, ensure_ascii=False, indent=2)

print(f"  ✓ Salvo: {output_ind}")

# ============================================================================
# 7. ESTATÍSTICAS GERAIS
# ============================================================================
print("\n[7/7] Calculando estatísticas gerais...")

# Carregar população
with open(DATA_DIR / 'populacao_ibge.json', 'r', encoding='utf-8') as f:
    pop_ibge = json.load(f)

pop_total = sum(m['populacao'] for m in pop_ibge)
area_total = df_indicadores['Area_Km2'].sum()

estatisticas_total = {
    "malha_total": {
        "extensao_total_km": round(extensao_total_km, 2),
        "extensao_osm_km": round(extensao_osm_km, 2),
        "extensao_der_km": round(extensao_der_km, 2),
        "participacao_osm_perc": round((extensao_osm_km / extensao_total_km) * 100, 2),
        "participacao_der_perc": round((extensao_der_km / extensao_total_km) * 100, 2),
        "num_segmentos_total": len(malha_total),
        "num_segmentos_osm": len(osm),
        "num_segmentos_der": len(der_utm)
    },
    "densidades_totais": {
        "densidade_espacial_10k": round((extensao_total_km / area_total) * 10_000, 4),
        "densidade_espacial_abs": round(extensao_total_km / area_total, 6),
        "densidade_populacional_10k": round((extensao_total_km / pop_total) * 10_000, 4)
    },
    "territorio": {
        "area_total_km2": round(area_total, 2),
        "populacao_total": pop_total,
        "num_municipios": 645
    }
}

output_stats = DATA_DIR / 'estatisticas_malha_total.json'
with open(output_stats, 'w', encoding='utf-8') as f:
    json.dump(estatisticas_total, f, ensure_ascii=False, indent=2)

print(f"  ✓ Salvo: {output_stats}")

# ============================================================================
# RESUMO FINAL
# ============================================================================
print("\n" + "=" * 80)
print("RESUMO FINAL - MALHA TOTAL ESTADUAL")
print("=" * 80)
print(f"\n📊 EXTENSÃO TOTAL:        {extensao_total_km:>10,.2f} km (100,0%)")
print(f"   ├─ OSM Vicinal:        {extensao_osm_km:>10,.2f} km ({(extensao_osm_km/extensao_total_km)*100:5.1f}%)")
print(f"   └─ DER Oficial:        {extensao_der_km:>10,.2f} km ({(extensao_der_km/extensao_total_km)*100:5.1f}%)")
print(f"\n🔢 SEGMENTOS TOTAIS:      {len(malha_total):>10,}")
print(f"   ├─ OSM:                {len(osm):>10,}")
print(f"   └─ DER:                {len(der_utm):>10,}")
print(f"\n📍 DENSIDADE ESPACIAL:    {estatisticas_total['densidades_totais']['densidade_espacial_10k']:>10,.2f} km/10.000km²")
print(f"👥 DENSIDADE POPULACIONAL: {estatisticas_total['densidades_totais']['densidade_populacional_10k']:>10,.2f} km/10.000 hab")
print(f"\n💡 RAZÃO OSM/DER:         {extensao_osm_km / extensao_der_km:>10,.2f}×")

print("\n" + "=" * 80)
print("✅ PROCESSAMENTO CONCLUÍDO!")
print("=" * 80)
print("\nArquivos gerados:")
print(f"  • {output_der}")
print(f"  • {output_total}")
print(f"  • {output_ind}")
print(f"  • {output_stats}")
print("=" * 80)
