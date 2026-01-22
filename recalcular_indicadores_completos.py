"""
Script para recalcular indicadores completos com dados reais do IBGE 2025
Aplica unidade de medida km/10.000km² para densidade espacial

Indicadores calculados:
- Densidade por área (km/10.000km² de área territorial)
- Densidade populacional (km/10.000 habitantes)
- Disparidades regionais (desvio da média estadual)
- Estatísticas descritivas completas
"""

import geopandas as gpd
import pandas as pd
import json
from pathlib import Path
import numpy as np

# Definir caminhos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'docs' / 'data'

print("=" * 70)
print("RECALCULANDO INDICADORES COM DADOS REAIS IBGE 2025")
print("=" * 70)

# ============================================================================
# 1. CARREGAR DADOS
# ============================================================================
print("\n[1/5] Carregando dados espaciais e populacionais...")

# Malha vicinal estimada por município
malha_mun = gpd.read_file(DATA_DIR / 'municipios_totais.geojson')
print(f"  [OK] {len(malha_mun)} municipios com malha vicinal")

# Dados populacionais reais IBGE 2025
with open(DATA_DIR / 'populacao_ibge.json', 'r', encoding='utf-8') as f:
    pop_ibge = json.load(f)
print(f"  [OK] {len(pop_ibge)} municipios com dados populacionais")

# Criar dicionário de população por código IBGE
pop_dict = {str(m['cod_ibge']): m['populacao'] for m in pop_ibge}

# ============================================================================
# 2. PREPARAR DADOS MUNICIPAIS
# ============================================================================
print("\n[2/5] Preparando dados municipais...")

# Calcular área em km² a partir da geometria
# Garantir CRS correto (SIRGAS 2000 / UTM zone 23S - EPSG:31983)
if malha_mun.crs.to_epsg() != 31983:
    malha_mun_proj = malha_mun.to_crs(epsg=31983)
else:
    malha_mun_proj = malha_mun

# Calcular área em km²
malha_mun_proj['Area_Km2'] = malha_mun_proj.geometry.area / 1_000_000

# Usar geometria original mas copiar área calculada
malha_mun['Area_Km2'] = malha_mun_proj['Area_Km2'].values

# Adicionar coluna RA se não existir
if 'RA' not in malha_mun.columns:
    # Tentar obter de municipios_sp.geojson
    try:
        municipios_sp = gpd.read_file(DATA_DIR / 'municipios_sp.geojson')
        ra_dict = dict(zip(municipios_sp['Cod_ibge'].astype(str), municipios_sp['RA']))
        malha_mun['RA'] = malha_mun['Cod_ibge'].astype(str).map(ra_dict)
    except:
        malha_mun['RA'] = 'São Paulo'  # fallback

# Garantir que Cod_ibge é string
malha_mun['Cod_ibge'] = malha_mun['Cod_ibge'].astype(str)

# Adicionar população real
malha_mun['Pop_2025'] = malha_mun['Cod_ibge'].map(pop_dict)

# Verificar municípios sem população
sem_pop = malha_mun[malha_mun['Pop_2025'].isna()]
if len(sem_pop) > 0:
    print(f"  [ALERTA] {len(sem_pop)} municipios sem dados de populacao")

# Preencher NaN com média (backup)
media_pop = malha_mun['Pop_2025'].mean()
malha_mun.loc[malha_mun['Pop_2025'].isna(), 'Pop_2025'] = media_pop

print(f"  [OK] Populacao total: {malha_mun['Pop_2025'].sum():,.0f} habitantes")
print(f"  [OK] Area total: {malha_mun['Area_Km2'].sum():,.2f} km²")

# ============================================================================
# 3. CALCULAR INDICADORES MUNICIPAIS
# ============================================================================
print("\n[3/5] Calculando indicadores municipais...")

# Densidade por área: km/10.000km²
# Fórmula: (extensao_km / Area_Km2) * 10000
malha_mun['densidade_area_10k'] = (malha_mun['extensao_km'] / malha_mun['Area_Km2']) * 10000

# Densidade populacional: km/10.000 habitantes
# Fórmula: (extensao_km / Pop_2025) * 10000
malha_mun['densidade_pop_10k'] = (malha_mun['extensao_km'] / malha_mun['Pop_2025']) * 10000

# Densidade absoluta (para referência): km/km²
malha_mun['densidade_area_abs'] = malha_mun['extensao_km'] / malha_mun['Area_Km2']

# Calcular disparidades de densidade espacial
media_dens_area = malha_mun['densidade_area_10k'].mean()
malha_mun['desvio_dens_area'] = ((malha_mun['densidade_area_10k'] - media_dens_area) / media_dens_area) * 100

# Calcular disparidades de densidade populacional
media_dens_pop = malha_mun['densidade_pop_10k'].mean()
malha_mun['desvio_dens_pop'] = ((malha_mun['densidade_pop_10k'] - media_dens_pop) / media_dens_pop) * 100

# Classificar disparidades espaciais
def classificar_disparidade(desvio):
    if desvio < -50:
        return 'Muito Abaixo'
    elif desvio < -20:
        return 'Abaixo'
    elif desvio <= 20:
        return 'Média'
    elif desvio <= 50:
        return 'Acima'
    else:
        return 'Muito Acima'

malha_mun['classe_disp_area'] = malha_mun['desvio_dens_area'].apply(classificar_disparidade)
malha_mun['classe_disp_pop'] = malha_mun['desvio_dens_pop'].apply(classificar_disparidade)

print(f"  [OK] Densidade media espacial: {media_dens_area:.2f} km/10.000km²")
print(f"  [OK] Densidade media populacional: {media_dens_pop:.2f} km/10.000 hab")

# ============================================================================
# 4. CALCULAR INDICADORES REGIONAIS
# ============================================================================
print("\n[4/5] Calculando indicadores regionais...")

# Agrupar por Região Administrativa
regioes_agg = malha_mun.groupby('RA').agg({
    'Cod_ibge': 'count',
    'Area_Km2': 'sum',
    'Pop_2025': 'sum',
    'extensao_km': 'sum'
}).rename(columns={'Cod_ibge': 'num_municipios'})

# Calcular densidades regionais
regioes_agg['densidade_area_10k'] = (regioes_agg['extensao_km'] / regioes_agg['Area_Km2']) * 10000
regioes_agg['densidade_pop_10k'] = (regioes_agg['extensao_km'] / regioes_agg['Pop_2025']) * 10000
regioes_agg['densidade_area_abs'] = regioes_agg['extensao_km'] / regioes_agg['Area_Km2']
regioes_agg['extensao_media_mun'] = regioes_agg['extensao_km'] / regioes_agg['num_municipios']

# Calcular disparidades regionais
media_regional_area = regioes_agg['densidade_area_10k'].mean()
media_regional_pop = regioes_agg['densidade_pop_10k'].mean()
regioes_agg['desvio_dens_area'] = ((regioes_agg['densidade_area_10k'] - media_regional_area) / media_regional_area) * 100
regioes_agg['desvio_dens_pop'] = ((regioes_agg['densidade_pop_10k'] - media_regional_pop) / media_regional_pop) * 100

print(f"  [OK] {len(regioes_agg)} regioes processadas")

# ============================================================================
# 5. SALVAR RESULTADOS
# ============================================================================
print("\n[5/5] Salvando resultados...")

# Preparar dados municipais para JSON
municipios_json = []
for _, row in malha_mun.iterrows():
    municipios_json.append({
        'Cod_ibge': row['Cod_ibge'],
        'Municipio': row['Municipio'],
        'RA': row['RA'],
        'Area_Km2': round(row['Area_Km2'], 2),
        'Pop_2025': int(row['Pop_2025']),
        'extensao_km': round(row['extensao_km'], 2),
        'densidade_area_10k': round(row['densidade_area_10k'], 4),
        'densidade_area_abs': round(row['densidade_area_abs'], 6),
        'densidade_pop_10k': round(row['densidade_pop_10k'], 4),
        'desvio_dens_area': round(row['desvio_dens_area'], 2),
        'desvio_dens_pop': round(row['desvio_dens_pop'], 2),
        'classe_disp_area': row['classe_disp_area'],
        'classe_disp_pop': row['classe_disp_pop']
    })

# Salvar dados municipais
output_mun = DATA_DIR / 'municipios_indicadores.json'
with open(output_mun, 'w', encoding='utf-8') as f:
    json.dump(municipios_json, f, ensure_ascii=False, indent=2)
print(f"  [SALVO] {output_mun}")

# Preparar dados regionais para JSON
regioes_json = []
for ra, row in regioes_agg.iterrows():
    regioes_json.append({
        'RA': ra,
        'num_municipios': int(row['num_municipios']),
        'area_km2': round(row['Area_Km2'], 2),
        'populacao': int(row['Pop_2025']),
        'extensao_km': round(row['extensao_km'], 2),
        'densidade_area_10k': round(row['densidade_area_10k'], 4),
        'densidade_area_abs': round(row['densidade_area_abs'], 6),
        'densidade_pop_10k': round(row['densidade_pop_10k'], 4),
        'extensao_media_mun': round(row['extensao_media_mun'], 2),
        'desvio_dens_area': round(row['desvio_dens_area'], 2),
        'desvio_dens_pop': round(row['desvio_dens_pop'], 2)
    })

# Salvar dados regionais
output_reg = DATA_DIR / 'regioes_indicadores.json'
with open(output_reg, 'w', encoding='utf-8') as f:
    json.dump(regioes_json, f, ensure_ascii=False, indent=2)
print(f"  [SALVO] {output_reg}")

# Estatísticas completas
estatisticas = {
    'municipal': {
        'extensao': {
            'total': round(malha_mun['extensao_km'].sum(), 2),
            'media': round(malha_mun['extensao_km'].mean(), 2),
            'mediana': round(malha_mun['extensao_km'].median(), 2),
            'desvio_padrao': round(malha_mun['extensao_km'].std(), 2),
            'minimo': round(malha_mun['extensao_km'].min(), 2),
            'maximo': round(malha_mun['extensao_km'].max(), 2),
            'q25': round(malha_mun['extensao_km'].quantile(0.25), 2),
            'q75': round(malha_mun['extensao_km'].quantile(0.75), 2)
        },
        'densidade_area_10k': {
            'media': round(malha_mun['densidade_area_10k'].mean(), 4),
            'mediana': round(malha_mun['densidade_area_10k'].median(), 4),
            'desvio_padrao': round(malha_mun['densidade_area_10k'].std(), 4),
            'minimo': round(malha_mun['densidade_area_10k'].min(), 4),
            'maximo': round(malha_mun['densidade_area_10k'].max(), 4)
        },
        'densidade_area_abs': {
            'media': round(malha_mun['densidade_area_abs'].mean(), 6),
            'mediana': round(malha_mun['densidade_area_abs'].median(), 6),
            'minimo': round(malha_mun['densidade_area_abs'].min(), 6),
            'maximo': round(malha_mun['densidade_area_abs'].max(), 6)
        },
        'densidade_pop_10k': {
            'media': round(malha_mun['densidade_pop_10k'].mean(), 4),
            'mediana': round(malha_mun['densidade_pop_10k'].median(), 4),
            'desvio_padrao': round(malha_mun['densidade_pop_10k'].std(), 4),
            'minimo': round(malha_mun['densidade_pop_10k'].min(), 4),
            'maximo': round(malha_mun['densidade_pop_10k'].max(), 4)
        }
    },
    'regional': {
        'extensao': {
            'total': round(regioes_agg['extensao_km'].sum(), 2),
            'media': round(regioes_agg['extensao_km'].mean(), 2),
            'minimo': round(regioes_agg['extensao_km'].min(), 2),
            'maximo': round(regioes_agg['extensao_km'].max(), 2)
        },
        'densidade_area_10k': {
            'media': round(regioes_agg['densidade_area_10k'].mean(), 4),
            'minimo': round(regioes_agg['densidade_area_10k'].min(), 4),
            'maximo': round(regioes_agg['densidade_area_10k'].max(), 4)
        },
        'densidade_pop_10k': {
            'media': round(regioes_agg['densidade_pop_10k'].mean(), 4),
            'minimo': round(regioes_agg['densidade_pop_10k'].min(), 4),
            'maximo': round(regioes_agg['densidade_pop_10k'].max(), 4)
        }
    },
    'geral': {
        'total_municipios': len(malha_mun),
        'municipios_com_dados': int((~malha_mun['extensao_km'].isna()).sum()),
        'populacao_total': int(malha_mun['Pop_2025'].sum()),
        'ano_referencia': '2025',
        'fonte': 'IBGE SIDRA - Tabela 6579',
        'extensao_total_km': round(malha_mun['extensao_km'].sum(), 2),
        'razao_max_min': round(malha_mun[malha_mun['extensao_km'] > 0]['extensao_km'].max() / malha_mun[malha_mun['extensao_km'] > 0]['extensao_km'].min(), 2) if malha_mun[malha_mun['extensao_km'] > 0]['extensao_km'].min() > 0 else None
    }
}

# Salvar estatísticas
output_stats = DATA_DIR / 'estatisticas_completas.json'
with open(output_stats, 'w', encoding='utf-8') as f:
    json.dump(estatisticas, f, ensure_ascii=False, indent=2)
print(f"  [SALVO] {output_stats}")

print("\n" + "=" * 70)
print("RESUMO DOS CALCULOS")
print("=" * 70)
print(f"Total de municipios: {len(municipios_json)}")
print(f"Total de regioes: {len(regioes_json)}")
print(f"Populacao total SP: {estatisticas['geral']['populacao_total']:,} habitantes")
print(f"Extensao total: {estatisticas['geral']['extensao_total_km']:,} km")
print(f"\nDensidade media espacial: {estatisticas['municipal']['densidade_area_10k']['media']:.4f} km/10.000km²")
print(f"Densidade media espacial (absoluta): {estatisticas['municipal']['densidade_area_abs']['media']:.6f} km/km²")
print(f"Densidade media populacional: {estatisticas['municipal']['densidade_pop_10k']['media']:.4f} km/10.000 hab")
print(f"\nRazao max/min: {estatisticas['geral']['razao_max_min']:.2f}×")
print("=" * 70)
print("[CONCLUIDO] Todos os indicadores foram recalculados com sucesso!")
print("=" * 70)
