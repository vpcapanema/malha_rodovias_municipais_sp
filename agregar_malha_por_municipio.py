"""
Agregar malha vicinal por município
Usa coluna 'metros' (não recalcula nada!)
"""
import geopandas as gpd
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'docs' / 'data'

print("=" * 70)
print("AGREGANDO MALHA VICINAL POR MUNICÍPIO")
print("=" * 70)

# Carregar malha vicinal completa
print("\n[1/4] Carregando malha_vicinais.geojson...")
malha = gpd.read_file(DATA_DIR / 'malha_vicinais.geojson')
print(f"  [OK] {len(malha)} segmentos")
print(f"  [OK] CRS: {malha.crs}")

# Verificar coluna metros
if 'metros' not in malha.columns:
    raise ValueError("Coluna 'metros' não encontrada!")

total_metros = malha['metros'].sum()
print(f"  [OK] Total: {total_metros:,.2f} metros = {total_metros/1000:,.2f} km")

# Carregar municípios
print("\n[2/4] Carregando municipios_sp.geojson...")
municipios = gpd.read_file(DATA_DIR / 'municipios_sp.geojson')
print(f"  [OK] {len(municipios)} municípios")

# Garantir Cod_ibge é string
municipios['Cod_ibge'] = municipios['Cod_ibge'].astype(str)
malha['Cod_ibge'] = malha['Cod_ibge'].astype(str)

print("\n[3/4] Agregando por município...")

# Agrupar por município e somar metros
agregado = malha.groupby('Cod_ibge').agg({
    'metros': 'sum',
    'Municipio': 'first',
    'GID_RA': 'first'
}).reset_index()

print(f"  [OK] {len(agregado)} municípios com rodovias")

# Calcular extensao_km a partir da coluna metros
agregado['extensao_km'] = agregado['metros'] / 1000

# Fazer merge com geometrias dos municípios
municipios_totais = municipios[['Cod_ibge', 'Municipio', 'RA', 'geometry']].merge(
    agregado[['Cod_ibge', 'extensao_km']],
    on='Cod_ibge',
    how='left'
)

# Preencher NaN com 0 (municípios sem rodovias)
municipios_totais['extensao_km'] = municipios_totais['extensao_km'].fillna(0)

# Converter para GeoDataFrame
municipios_totais = gpd.GeoDataFrame(municipios_totais, geometry='geometry', crs=municipios.crs)

print(f"  [OK] {len(municipios_totais)} municípios no total")
print(f"  [OK] {(municipios_totais['extensao_km'] > 0).sum()} municípios com rodovias")
print(f"  [OK] {(municipios_totais['extensao_km'] == 0).sum()} municípios sem rodovias")

# Verificar total
total_km = municipios_totais['extensao_km'].sum()
print(f"\n[VALIDAÇÃO]")
print(f"  Total agregado: {total_km:,.2f} km")
print(f"  Total esperado: {total_metros/1000:,.2f} km")
print(f"  Diferença: {abs(total_km - total_metros/1000):.6f} km")

if abs(total_km - total_metros/1000) < 0.01:
    print(f"  ✅ VALORES CONFEREM!")
else:
    print(f"  ⚠️  DIFERENÇA DETECTADA!")

print("\n[4/4] Salvando municipios_totais.geojson...")
output_file = DATA_DIR / 'municipios_totais.geojson'
municipios_totais.to_file(output_file, driver='GeoJSON')

print(f"  [OK] Salvo: {output_file}")
print(f"  [OK] Tamanho: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

print("\n" + "=" * 70)
print("CONCLUÍDO!")
print("=" * 70)
print(f"\n✅ Total exato: {total_km:,.2f} km")
print(f"✅ {len(municipios_totais)} municípios processados")
