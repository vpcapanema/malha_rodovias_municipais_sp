"""
Analisar dados de pavimentação da malha DER e criar estatísticas 
comparativas com a malha OSM vicinal
"""

import geopandas as gpd
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DER_DIR = BASE_DIR / 'docs' / 'Sistema Rodoviário Estadual'
DATA_DIR = BASE_DIR / 'docs' / 'data'

print("="*80)
print("ANÁLISE DE PAVIMENTAÇÃO - MALHA DER")
print("="*80)

# Carregar DER shapefile
print("\n[1/3] Carregando shapefile DER...")
der = gpd.read_file(DER_DIR / 'MALHA_RODOVIARIA.shp')
print(f"  ✓ Carregado: {len(der)} segmentos")

# Converter para EPSG:31983
print("\n[2/3] Analisando pavimentação...")
der = der.to_crs(31983)

# Analisar coluna TipoPista
print("\n  Valores encontrados em 'TipoPista':")
print(der['TipoPista'].value_counts())

# Calcular extensões por tipo
der['extensao_m'] = der.geometry.length
der['extensao_km'] = der['extensao_m'] / 1000

# Classificar pavimentação
# Baseado nos valores típicos: Pista Dupla, Pista Simples = Pavimentado
# Leito Natural, etc = Não pavimentado
def classificar_pavimentacao_der(tipo_pista):
    """Classifica se é pavimentado ou não baseado no TipoPista"""
    tipo = str(tipo_pista).lower() if tipo_pista else ''
    
    # Pavimentado
    if any(x in tipo for x in ['dupla', 'simples', 'paviment']):
        return 'pavimentado'
    # Não pavimentado
    elif any(x in tipo for x in ['natural', 'leito', 'implant']):
        return 'nao_pavimentado'
    else:
        # Se não conseguir classificar, assumir pavimentado (DER geralmente é pavimentado)
        return 'pavimentado'

der['classificacao_pav'] = der['TipoPista'].apply(classificar_pavimentacao_der)

# Estatísticas DER
stats_der = der.groupby('classificacao_pav').agg({
    'extensao_km': 'sum',
    'Rodovia': 'count'
}).round(2)

print("\n  Estatísticas DER:")
print(stats_der)

extensao_pav_der = der[der['classificacao_pav'] == 'pavimentado']['extensao_km'].sum()
extensao_nao_pav_der = der[der['classificacao_pav'] == 'nao_pavimentado']['extensao_km'].sum()
extensao_total_der = extensao_pav_der + extensao_nao_pav_der

pct_pav_der = (extensao_pav_der / extensao_total_der) * 100
pct_nao_pav_der = (extensao_nao_pav_der / extensao_total_der) * 100

print(f"\n  Pavimentado: {extensao_pav_der:,.2f} km ({pct_pav_der:.1f}%)")
print(f"  Não pavimentado: {extensao_nao_pav_der:,.2f} km ({pct_nao_pav_der:.1f}%)")
print(f"  Total: {extensao_total_der:,.2f} km")

# Carregar estatísticas OSM
print("\n[3/3] Carregando estatísticas OSM...")
with open(DATA_DIR / 'segmentos_estatisticas.json', 'r', encoding='utf-8') as f:
    stats_osm = json.load(f)

# Extrair dados de pavimentação OSM
dist_tipo = stats_osm.get('distribuicao_por_tipo', [])

# Tipo 8 = Pavimentado, Tipo 9 = Não pavimentado (terra/cascalho)
extensao_pav_osm = sum(d['extensao_km'] for d in dist_tipo if str(d.get('tipo')) == '8')
extensao_nao_pav_osm = sum(d['extensao_km'] for d in dist_tipo if str(d.get('tipo')) == '9')
extensao_outros_osm = sum(d['extensao_km'] for d in dist_tipo if str(d.get('tipo')) not in ['8', '9'])

extensao_total_osm = extensao_pav_osm + extensao_nao_pav_osm + extensao_outros_osm

print(f"  OSM Pavimentado: {extensao_pav_osm:,.2f} km")
print(f"  OSM Não pavimentado: {extensao_nao_pav_osm:,.2f} km")
print(f"  OSM Outros: {extensao_outros_osm:,.2f} km")
print(f"  OSM Total: {extensao_total_osm:,.2f} km")

# Calcular totais combinados
extensao_pav_total = extensao_pav_osm + extensao_pav_der
extensao_nao_pav_total = extensao_nao_pav_osm + extensao_nao_pav_der
extensao_total = extensao_total_osm + extensao_total_der

pct_pav_total = (extensao_pav_total / extensao_total) * 100
pct_nao_pav_total = (extensao_nao_pav_total / extensao_total) * 100

# Criar JSON de saída
output = {
    "osm_vicinal": {
        "pavimentado_km": round(extensao_pav_osm, 2),
        "nao_pavimentado_km": round(extensao_nao_pav_osm, 2),
        "outros_km": round(extensao_outros_osm, 2),
        "total_km": round(extensao_total_osm, 2),
        "pct_pavimentado": round((extensao_pav_osm / extensao_total_osm) * 100, 1),
        "pct_nao_pavimentado": round((extensao_nao_pav_osm / extensao_total_osm) * 100, 1),
        "pct_outros": round((extensao_outros_osm / extensao_total_osm) * 100, 1)
    },
    "der_oficial": {
        "pavimentado_km": round(extensao_pav_der, 2),
        "nao_pavimentado_km": round(extensao_nao_pav_der, 2),
        "total_km": round(extensao_total_der, 2),
        "pct_pavimentado": round(pct_pav_der, 1),
        "pct_nao_pavimentado": round(pct_nao_pav_der, 1)
    },
    "malha_total": {
        "pavimentado_km": round(extensao_pav_total, 2),
        "nao_pavimentado_km": round(extensao_nao_pav_total, 2),
        "outros_km": round(extensao_outros_osm, 2),
        "total_km": round(extensao_total, 2),
        "pct_pavimentado": round(pct_pav_total, 1),
        "pct_nao_pavimentado": round(pct_nao_pav_total, 1),
        "pct_outros": round((extensao_outros_osm / extensao_total) * 100, 1)
    }
}

# Salvar JSON
output_file = DATA_DIR / 'pavimentacao_comparada.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n" + "="*80)
print("RESUMO COMPARATIVO DE PAVIMENTAÇÃO")
print("="*80)

print("\n📊 MALHA OSM VICINAL:")
print(f"  Pavimentado:     {extensao_pav_osm:>10,.2f} km ({(extensao_pav_osm/extensao_total_osm)*100:>5.1f}%)")
print(f"  Não pavimentado: {extensao_nao_pav_osm:>10,.2f} km ({(extensao_nao_pav_osm/extensao_total_osm)*100:>5.1f}%)")
print(f"  Outros:          {extensao_outros_osm:>10,.2f} km ({(extensao_outros_osm/extensao_total_osm)*100:>5.1f}%)")
print(f"  Total:           {extensao_total_osm:>10,.2f} km")

print("\n🛣️  MALHA DER OFICIAL:")
print(f"  Pavimentado:     {extensao_pav_der:>10,.2f} km ({pct_pav_der:>5.1f}%)")
print(f"  Não pavimentado: {extensao_nao_pav_der:>10,.2f} km ({pct_nao_pav_der:>5.1f}%)")
print(f"  Total:           {extensao_total_der:>10,.2f} km")

print("\n🌐 MALHA TOTAL (OSM + DER):")
print(f"  Pavimentado:     {extensao_pav_total:>10,.2f} km ({pct_pav_total:>5.1f}%)")
print(f"  Não pavimentado: {extensao_nao_pav_total:>10,.2f} km ({pct_nao_pav_total:>5.1f}%)")
print(f"  Outros:          {extensao_outros_osm:>10,.2f} km ({(extensao_outros_osm/extensao_total)*100:>5.1f}%)")
print(f"  Total:           {extensao_total:>10,.2f} km")

print("\n✅ Arquivo salvo: " + str(output_file))
print("="*80)
