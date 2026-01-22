"""
Script para calcular estatísticas dos segmentos viários individuais
da malha vicinal estimada
"""

import geopandas as gpd
import json
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'docs' / 'data'

print("=" * 70)
print("CALCULANDO ESTATÍSTICAS DOS SEGMENTOS VIÁRIOS")
print("=" * 70)

# Carregar malha vicinal completa
malha_file = DATA_DIR / 'malha_vicinais.geojson'
print(f"\n[LOAD] Carregando {malha_file.name}...")

malha = gpd.read_file(malha_file)
print(f"[OK] {len(malha)} segmentos carregados")

# USAR COLUNA 'metros' (fonte de verdade calculada em UTM 23S pelo Silvio)
if 'metros' in malha.columns:
    print("[OK] Usando coluna 'metros' (UTM 23S - fonte de verdade)")
    comprimentos_km = malha['metros'] / 1000
    malha['comp_km'] = comprimentos_km
else:
    print("[ERRO] Coluna 'metros' não encontrada!")
    raise ValueError("GeoJSON deve ter coluna 'metros' com comprimentos pré-calculados")

# Calcular estatísticas
stats = {
    'total_segmentos': int(len(malha)),
    'extensao_total_km': round(float(comprimentos_km.sum()), 2),
    'comprimento_medio_km': round(float(comprimentos_km.mean()), 2),
    'comprimento_mediano_km': round(float(comprimentos_km.median()), 2),
    'desvio_padrao_km': round(float(comprimentos_km.std()), 2),
    'minimo_km': round(float(comprimentos_km.min()), 2),
    'maximo_km': round(float(comprimentos_km.max()), 2),
    'q25_km': round(float(comprimentos_km.quantile(0.25)), 2),
    'q75_km': round(float(comprimentos_km.quantile(0.75)), 2),
    'amplitude_km': round(float(comprimentos_km.max() - comprimentos_km.min()), 2)
}

# Distribuição por faixas
faixas = [
    (0, 2, '0-2 km'),
    (2, 5, '2-5 km'),
    (5, 10, '5-10 km'),
    (10, 20, '10-20 km'),
    (20, 40, '20-40 km')
]

distribuicao = []
for min_val, max_val, label in faixas:
    mask = (comprimentos_km >= min_val) & (comprimentos_km < max_val)
    count = int(mask.sum())
    extensao = round(float(comprimentos_km[mask].sum()), 2)
    perc_count = round((count / len(malha)) * 100, 1)
    perc_ext = round((extensao / comprimentos_km.sum()) * 100, 1)
    
    distribuicao.append({
        'faixa': label,
        'quantidade': count,
        'percentual_quantidade': perc_count,
        'extensao_km': extensao,
        'percentual_extensao': perc_ext
    })

# Tipo de superfície/pavimento - USAR COLUNA sup_tipo_c
if 'sup_tipo_c' in malha.columns:
    print("[INFO] Analisando coluna: sup_tipo_c")
    
    tipos_dist = malha.groupby('sup_tipo_c').agg({
        'comp_km': ['count', 'sum']
    }).reset_index()
    tipos_dist.columns = ['tipo', 'quantidade', 'extensao_km']
    tipos_dist['percentual_quantidade'] = round((tipos_dist['quantidade'] / len(malha)) * 100, 1)
    tipos_dist['percentual_extensao'] = round((tipos_dist['extensao_km'] / comprimentos_km.sum()) * 100, 1)
    tipos_dist['extensao_km'] = tipos_dist['extensao_km'].round(2)
    
    distribuicao_tipos = tipos_dist.to_dict('records')
else:
    distribuicao_tipos = []
    print("[ALERTA] Coluna 'sup_tipo_c' não encontrada")

# Salvar resultados
output = {
    'estatisticas_segmentos': stats,
    'distribuicao_por_faixas': distribuicao,
    'distribuicao_por_tipo': distribuicao_tipos
}

output_file = DATA_DIR / 'segmentos_estatisticas.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print("RESUMO DAS ESTATÍSTICAS")
print("=" * 70)
print(f"Total de segmentos: {stats['total_segmentos']:,}")
print(f"Extensão total: {stats['extensao_total_km']:,} km")
print(f"\nComprimento médio: {stats['comprimento_medio_km']} km")
print(f"Comprimento mediano: {stats['comprimento_mediano_km']} km")
print(f"Desvio padrão: {stats['desvio_padrao_km']} km")
print(f"Amplitude: {stats['minimo_km']} - {stats['maximo_km']} km")
print(f"\n[SALVO] {output_file}")
print("=" * 70)
