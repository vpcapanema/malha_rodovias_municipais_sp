"""
Gerar métricas espaciais por município e Região Administrativa para a MALHA TOTAL
(OSM Vicinal + DER Oficial)
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

# Configuração
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'docs' / 'data'

print("="*80)
print("GERAÇÃO DE MÉTRICAS ESPACIAIS - MALHA TOTAL ESTADUAL")
print("="*80)

# ============================================================================
# 1. CARREGAR DADOS
# ============================================================================
print("\n[1/4] Carregando dados...")

# Carregar indicadores municipais da malha total
with open(DATA_DIR / 'municipios_indicadores_total.json', 'r', encoding='utf-8') as f:
    municipios_total = json.load(f)

df_mun = pd.DataFrame(municipios_total)
print(f"  ✓ Carregados: {len(df_mun)} municípios")

# Verificar colunas necessárias
required_cols = ['Cod_ibge', 'Municipio', 'RA', 'Area_Km2', 'Pop_2025', 
                 'extensao_km', 'extensao_total_km']
missing_cols = [col for col in required_cols if col not in df_mun.columns]
if missing_cols:
    print(f"  ✗ ERRO: Colunas ausentes: {missing_cols}")
    exit(1)

# ============================================================================
# 2. CALCULAR MÉTRICAS MUNICIPAIS COMPLETAS
# ============================================================================
print("\n[2/4] Calculando métricas municipais completas...")

# Densidade da malha total (adicional à malha vicinal OSM)
df_mun['densidade_total_area_10k'] = (df_mun['extensao_total_km'] / df_mun['Area_Km2']) * 10000
df_mun['densidade_total_area_abs'] = df_mun['extensao_total_km'] / df_mun['Area_Km2']
df_mun['densidade_total_pop_10k'] = (df_mun['extensao_total_km'] / df_mun['Pop_2025']) * 10000

# Calcular desvios em relação às médias estaduais
media_dens_area_total = df_mun['densidade_total_area_10k'].mean()
media_dens_pop_total = df_mun['densidade_total_pop_10k'].mean()

df_mun['desvio_total_dens_area'] = ((df_mun['densidade_total_area_10k'] - media_dens_area_total) / media_dens_area_total) * 100
df_mun['desvio_total_dens_pop'] = ((df_mun['densidade_total_pop_10k'] - media_dens_pop_total) / media_dens_pop_total) * 100

# Classificação de disponibilidade
def classificar_disponibilidade(desvio):
    if desvio >= 50:
        return "Muito Acima"
    elif desvio >= 15:
        return "Acima"
    elif desvio >= -15:
        return "Média"
    elif desvio >= -50:
        return "Abaixo"
    else:
        return "Muito Abaixo"

df_mun['classe_total_disp_area'] = df_mun['desvio_total_dens_area'].apply(classificar_disponibilidade)
df_mun['classe_total_disp_pop'] = df_mun['desvio_total_dens_pop'].apply(classificar_disponibilidade)

# Arredondar valores
df_mun['densidade_total_area_10k'] = df_mun['densidade_total_area_10k'].round(4)
df_mun['densidade_total_area_abs'] = df_mun['densidade_total_area_abs'].round(6)
df_mun['densidade_total_pop_10k'] = df_mun['densidade_total_pop_10k'].round(4)
df_mun['desvio_total_dens_area'] = df_mun['desvio_total_dens_area'].round(2)
df_mun['desvio_total_dens_pop'] = df_mun['desvio_total_dens_pop'].round(2)

print(f"  ✓ Métricas calculadas para {len(df_mun)} municípios")
print(f"    Média densidade área total: {media_dens_area_total:.2f} km/10k km²")
print(f"    Média densidade pop total: {media_dens_pop_total:.2f} km/10k hab")

# ============================================================================
# 3. AGREGAR POR REGIÃO ADMINISTRATIVA
# ============================================================================
print("\n[3/4] Agregando por Região Administrativa...")

# Agrupar por RA
regioes = df_mun.groupby('RA').agg({
    'Municipio': 'count',
    'Area_Km2': 'sum',
    'Pop_2025': 'sum',
    'extensao_km': 'sum',
    'extensao_total_km': 'sum'
}).reset_index()

regioes.columns = ['RA', 'num_municipios', 'area_km2', 'populacao', 
                   'extensao_osm_km', 'extensao_total_km']

# Calcular densidades para malha total
regioes['densidade_total_area_10k'] = (regioes['extensao_total_km'] / regioes['area_km2']) * 10000
regioes['densidade_total_area_abs'] = regioes['extensao_total_km'] / regioes['area_km2']
regioes['densidade_total_pop_10k'] = (regioes['extensao_total_km'] / regioes['populacao']) * 10000

# Calcular médias por município
regioes['extensao_total_media_mun'] = regioes['extensao_total_km'] / regioes['num_municipios']

# Calcular desvios
media_dens_area_ra = regioes['densidade_total_area_10k'].mean()
media_dens_pop_ra = regioes['densidade_total_pop_10k'].mean()

regioes['desvio_total_dens_area'] = ((regioes['densidade_total_area_10k'] - media_dens_area_ra) / media_dens_area_ra) * 100
regioes['desvio_total_dens_pop'] = ((regioes['densidade_total_pop_10k'] - media_dens_pop_ra) / media_dens_pop_ra) * 100

# Manter também densidades da malha OSM vicinal para comparação
regioes['densidade_osm_area_10k'] = (regioes['extensao_osm_km'] / regioes['area_km2']) * 10000
regioes['densidade_osm_pop_10k'] = (regioes['extensao_osm_km'] / regioes['populacao']) * 10000

# Arredondar valores
regioes['area_km2'] = regioes['area_km2'].round(2)
regioes['extensao_osm_km'] = regioes['extensao_osm_km'].round(2)
regioes['extensao_total_km'] = regioes['extensao_total_km'].round(2)
regioes['densidade_total_area_10k'] = regioes['densidade_total_area_10k'].round(4)
regioes['densidade_total_area_abs'] = regioes['densidade_total_area_abs'].round(6)
regioes['densidade_total_pop_10k'] = regioes['densidade_total_pop_10k'].round(4)
regioes['densidade_osm_area_10k'] = regioes['densidade_osm_area_10k'].round(4)
regioes['densidade_osm_pop_10k'] = regioes['densidade_osm_pop_10k'].round(4)
regioes['extensao_total_media_mun'] = regioes['extensao_total_media_mun'].round(2)
regioes['desvio_total_dens_area'] = regioes['desvio_total_dens_area'].round(2)
regioes['desvio_total_dens_pop'] = regioes['desvio_total_dens_pop'].round(2)

# Ordenar por extensão total
regioes = regioes.sort_values('extensao_total_km', ascending=False)

print(f"  ✓ Agregação concluída para {len(regioes)} regiões")

# ============================================================================
# 4. SALVAR ARQUIVOS
# ============================================================================
print("\n[4/4] Salvando arquivos...")

# Salvar indicadores municipais atualizados
municipios_output = df_mun.to_dict('records')
output_mun = DATA_DIR / 'municipios_indicadores_total.json'
with open(output_mun, 'w', encoding='utf-8') as f:
    json.dump(municipios_output, f, ensure_ascii=False, indent=2)
print(f"  ✓ Salvo: {output_mun}")

# Salvar indicadores regionais
regioes_output = regioes.to_dict('records')
output_ra = DATA_DIR / 'regioes_indicadores_total.json'
with open(output_ra, 'w', encoding='utf-8') as f:
    json.dump(regioes_output, f, ensure_ascii=False, indent=2)
print(f"  ✓ Salvo: {output_ra}")

# ============================================================================
# RESUMO FINAL
# ============================================================================
print("\n" + "="*80)
print("RESUMO DAS MÉTRICAS - MALHA TOTAL ESTADUAL")
print("="*80)

print(f"\n📊 TOTAL ESTADUAL:")
print(f"   Extensão OSM Vicinal:     {df_mun['extensao_km'].sum():,.2f} km")
print(f"   Extensão Total (OSM+DER): {df_mun['extensao_total_km'].sum():,.2f} km")
print(f"   Incremento DER:           {(df_mun['extensao_total_km'].sum() - df_mun['extensao_km'].sum()):,.2f} km")

print(f"\n📍 DENSIDADES MÉDIAS:")
print(f"   Densidade área total:     {media_dens_area_total:.2f} km/10k km²")
print(f"   Densidade pop total:      {media_dens_pop_total:.2f} km/10k hab")

print(f"\n🏆 TOP 5 REGIÕES (por extensão total):")
for i, row in regioes.head(5).iterrows():
    print(f"   {row['RA']:30s}  {row['extensao_total_km']:>8,.2f} km  ({row['num_municipios']:>3} municípios)")

print(f"\n📂 ARQUIVOS GERADOS:")
print(f"   • {output_mun}")
print(f"   • {output_ra}")

print("\n" + "="*80)
print("✅ PROCESSAMENTO CONCLUÍDO!")
print("="*80)
