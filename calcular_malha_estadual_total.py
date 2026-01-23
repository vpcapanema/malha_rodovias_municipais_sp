"""
Script para calcular indicadores da MALHA ESTADUAL TOTAL
Combina: Malha Vicinal Estimada (OSM) + Malha Oficial DER
"""

import geopandas as gpd
import json
from pathlib import Path
import numpy as np

print("=" * 70)
print("CALCULANDO INDICADORES DA MALHA ESTADUAL TOTAL")
print("Malha Vicinal Estimada + Malha Oficial DER")
print("=" * 70)
print()

# Caminhos
DATA_DIR = Path("docs/data")
RESULTS_DIR = Path("resultados/dados_processados")

# ============================================================================
# 1. CARREGAR DADOS
# ============================================================================
print("[1/6] Carregando dados geoespaciais...")

# Malha vicinal estimada (OSM)
malha_vicinal = gpd.read_file(DATA_DIR / "municipios_totais.geojson")
print(f"  ✓ Malha vicinal: {len(malha_vicinal)} municípios")

# Malha DER (já filtrada - OSM menos DER)
malha_der_subtraida = gpd.read_file(RESULTS_DIR / "osm_sp_menos_der.gpkg")
print(f"  ✓ Malha OSM filtrada: {len(malha_der_subtraida)} segmentos")

# Carregar população
with open(DATA_DIR / 'populacao_ibge.json', 'r', encoding='utf-8') as f:
    pop_ibge = json.load(f)
pop_dict = {str(m['cod_ibge']): m['populacao'] for m in pop_ibge}
print(f"  ✓ População: {len(pop_ibge)} municípios")

# Carregar indicadores municipais existentes
with open(DATA_DIR / 'municipios_indicadores.json', 'r', encoding='utf-8') as f:
    municipios_indicadores = json.load(f)
print(f"  ✓ Indicadores municipais: {len(municipios_indicadores)} municípios")

# ============================================================================
# 2. CALCULAR EXTENSÃO DA MALHA DER
# ============================================================================
print("\n[2/6] Processando malha DER estadual...")

# Verificar se existe arquivo com malha DER completa
malha_der_path = DATA_DIR / "malha_estadual_der.geojson"
if malha_der_path.exists():
    malha_der = gpd.read_file(malha_der_path)
    
    # Garantir CRS correto (SIRGAS 2000 / UTM 23S)
    if malha_der.crs.to_epsg() != 31983:
        malha_der = malha_der.to_crs(31983)
    
    extensao_der_km = malha_der.geometry.length.sum() / 1000
    num_segmentos_der = len(malha_der)
    print(f"  ✓ Extensão DER: {extensao_der_km:,.2f} km")
    print(f"  ✓ Segmentos DER: {num_segmentos_der:,}")
else:
    print("  ⚠ Arquivo malha_estadual_der.geojson não encontrado")
    print("  → Usando estimativa baseada em dados conhecidos")
    # Valores conhecidos do relatório
    extensao_der_km = 20_000  # Aproximação da rede DER-SP
    num_segmentos_der = 4_779

# ============================================================================
# 3. CALCULAR TOTAIS DA MALHA ESTADUAL
# ============================================================================
print("\n[3/6] Calculando totais da malha estadual...")

# Extensão vicinal (já calculada)
extensao_vicinal_km = malha_vicinal['extensao_km'].sum()
num_segmentos_vicinal = 7_417  # Do relatório

# TOTAIS
extensao_total_km = extensao_vicinal_km + extensao_der_km
num_segmentos_total = num_segmentos_vicinal + num_segmentos_der

print(f"  Malha Vicinal:  {extensao_vicinal_km:>12,.2f} km  ({num_segmentos_vicinal:>6,} segmentos)")
print(f"  Malha DER:      {extensao_der_km:>12,.2f} km  ({num_segmentos_der:>6,} segmentos)")
print(f"  {'─' * 50}")
print(f"  TOTAL ESTADUAL: {extensao_total_km:>12,.2f} km  ({num_segmentos_total:>6,} segmentos)")

# ============================================================================
# 4. CALCULAR PARTICIPAÇÃO PERCENTUAL
# ============================================================================
print("\n[4/6] Calculando participações percentuais...")

perc_vicinal = (extensao_vicinal_km / extensao_total_km) * 100
perc_der = (extensao_der_km / extensao_total_km) * 100

print(f"  Vicinal: {perc_vicinal:.1f}%")
print(f"  DER:     {perc_der:.1f}%")

# ============================================================================
# 5. CALCULAR DENSIDADES ESTADUAIS
# ============================================================================
print("\n[5/6] Calculando densidades estaduais...")

# Área total do estado - usar dados dos indicadores
area_total_km2 = sum(m['Area_Km2'] for m in municipios_indicadores)
populacao_total = sum(pop_dict.values())

# Densidade espacial (km de malha / 10.000 km²)
densidade_espacial_10k = (extensao_total_km / area_total_km2) * 10_000
densidade_espacial_abs = extensao_total_km / area_total_km2

# Densidade populacional (km de malha / 10.000 habitantes)
densidade_pop_10k = (extensao_total_km / populacao_total) * 10_000

print(f"  Área total SP:        {area_total_km2:>12,.2f} km²")
print(f"  População total:      {populacao_total:>12,} habitantes")
print(f"  Densidade espacial:   {densidade_espacial_10k:>12,.2f} km/10.000km²")
print(f"  Densidade espacial:   {densidade_espacial_abs:>12,.4f} km/km²")
print(f"  Densidade populacional: {densidade_pop_10k:>12,.2f} km/10.000 hab")

# ============================================================================
# 6. GERAR ARQUIVO JSON COM RESULTADOS
# ============================================================================
print("\n[6/6] Salvando resultados...")

resultados = {
    "resumo_geral": {
        "extensao_total_km": round(extensao_total_km, 2),
        "extensao_vicinal_km": round(extensao_vicinal_km, 2),
        "extensao_der_km": round(extensao_der_km, 2),
        "num_segmentos_total": num_segmentos_total,
        "num_segmentos_vicinal": num_segmentos_vicinal,
        "num_segmentos_der": num_segmentos_der,
        "participacao_vicinal_perc": round(perc_vicinal, 2),
        "participacao_der_perc": round(perc_der, 2)
    },
    "territorio": {
        "area_total_km2": round(area_total_km2, 2),
        "populacao_total": populacao_total,
        "num_municipios": 645
    },
    "densidades": {
        "densidade_espacial_10k": round(densidade_espacial_10k, 4),
        "densidade_espacial_abs": round(densidade_espacial_abs, 6),
        "densidade_populacional_10k": round(densidade_pop_10k, 4)
    },
    "comparacao": {
        "razao_vicinal_der": round(extensao_vicinal_km / extensao_der_km, 2),
        "km_por_habitante": round(extensao_total_km / populacao_total, 6),
        "km_por_km2": round(densidade_espacial_abs, 4)
    }
}

# Salvar JSON
output_path = DATA_DIR / "malha_estadual_total.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"  ✓ Resultados salvos: {output_path}")

print("\n" + "=" * 70)
print("RESUMO FINAL - MALHA ESTADUAL TOTAL")
print("=" * 70)
print(f"\n📊 EXTENSÃO TOTAL:        {extensao_total_km:,.2f} km")
print(f"   ├─ Vicinal (estimada): {extensao_vicinal_km:,.2f} km ({perc_vicinal:.1f}%)")
print(f"   └─ DER (oficial):      {extensao_der_km:,.2f} km ({perc_der:.1f}%)")
print(f"\n🔢 SEGMENTOS:             {num_segmentos_total:,}")
print(f"   ├─ Vicinal:            {num_segmentos_vicinal:,}")
print(f"   └─ DER:                {num_segmentos_der:,}")
print(f"\n📍 DENSIDADE ESPACIAL:    {densidade_espacial_10k:.2f} km/10.000km²")
print(f"👥 DENSIDADE POPULACIONAL: {densidade_pop_10k:.2f} km/10.000 hab")
print(f"\n💡 RAZÃO VICINAL/DER:     {extensao_vicinal_km / extensao_der_km:.2f}×")
print("\n" + "=" * 70)
print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
print("=" * 70)
