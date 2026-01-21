import geopandas as gpd
import json
import os

print("="*60)
print("PREPARANDO DADOS PARA MAPAS")
print("="*60)

# Criar pasta de saída
os.makedirs("app_web/data", exist_ok=True)

# ============================================================================
# 1. MALHA VICINAL OSM (simplificada para web)
# ============================================================================
print("\n1. Carregando malha OSM...")
osm = gpd.read_file("dados/vicinais_sp.gpkg")
print(f"   Total: {len(osm)} segmentos")

# Simplificar MUITO para performance
osm_simple = osm.copy()
osm_simple['geometry'] = osm_simple.geometry.simplify(0.005, preserve_topology=True)

# Salvar
osm_json = osm_simple.to_json()
with open("app_web/data/malha_osm.geojson", 'w', encoding='utf-8') as f:
    f.write(osm_json)
print(f"   ✓ Salvo: {len(osm_json)/1024/1024:.1f} MB")

# ============================================================================
# 2. MALHA DER
# ============================================================================
print("\n2. Carregando malha DER...")
try:
    der = gpd.read_file("dados/Sistema Rodoviário Estadual/TRECHOS_2024.shp")
    print(f"   Total: {len(der)} segmentos DER")
    
    # Filtrar apenas vicinais municipais
    der_vic = der[der['JURISDICAO'].isin(['MUNICIPAL', 'Município', 'MUNICIPIO'])].copy()
    print(f"   Vicinais municipais: {len(der_vic)}")
    
    # Simplificar
    der_vic['geometry'] = der_vic.geometry.simplify(0.005, preserve_topology=True)
    
    # Salvar
    der_json = der_vic.to_json()
    with open("app_web/data/malha_der.geojson", 'w', encoding='utf-8') as f:
        f.write(der_json)
    print(f"   ✓ Salvo: {len(der_json)/1024/1024:.1f} MB")
except Exception as e:
    print(f"   ⚠ Erro ao carregar DER: {e}")
    print("   Tentando arquivo alternativo...")
    try:
        der_vic = gpd.read_file("dados/vicinais_simples.gpkg")
        der_vic['geometry'] = der_vic.geometry.simplify(0.005, preserve_topology=True)
        der_json = der_vic.to_json()
        with open("app_web/data/malha_der.geojson", 'w', encoding='utf-8') as f:
            f.write(der_json)
        print(f"   ✓ Salvo: {len(der_json)/1024/1024:.1f} MB")
    except Exception as e2:
        print(f"   ✗ Erro: {e2}")

# ============================================================================
# 3. MUNICÍPIOS DE SP (polígonos)
# ============================================================================
print("\n3. Carregando municípios...")
municipios = gpd.read_file("dados/malha_municipal_sp.gpkg")
print(f"   Total: {len(municipios)} municípios")

# Simplificar polígonos
municipios_simple = municipios.copy()
municipios_simple['geometry'] = municipios_simple.geometry.simplify(0.01, preserve_topology=True)

# Salvar
mun_json = municipios_simple.to_json()
with open("app_web/data/municipios_sp.geojson", 'w', encoding='utf-8') as f:
    f.write(mun_json)
print(f"   ✓ Salvo: {len(mun_json)/1024/1024:.1f} MB")

# ============================================================================
# 4. REGIÕES ADMINISTRATIVAS (dissolver municípios)
# ============================================================================
print("\n4. Criando Regiões Administrativas...")
if 'ra_nome' in municipios.columns:
    ras = municipios.dissolve(by='ra_nome', as_index=False)
    print(f"   Total: {len(ras)} RAs")
    
    # Simplificar
    ras['geometry'] = ras.geometry.simplify(0.015, preserve_topology=True)
    
    # Salvar
    ras_json = ras.to_json()
    with open("app_web/data/regioes_admin.geojson", 'w', encoding='utf-8') as f:
        f.write(ras_json)
    print(f"   ✓ Salvo: {len(ras_json)/1024/1024:.1f} MB")
else:
    print("   ⚠ Coluna 'ra_nome' não encontrada")

# ============================================================================
# 5. INDICADORES (Estado, RA, Município)
# ============================================================================
print("\n5. Calculando indicadores...")

# Intersectar vicinais com municípios
print("   Intersectando OSM com municípios...")
osm_mun = gpd.overlay(osm, municipios, how='intersection')
osm_mun['extensao_km'] = osm_mun.geometry.length / 1000

# Calcular por município
ind_mun = osm_mun.groupby('CD_MUN').agg({
    'extensao_km': 'sum',
    'geometry': 'first'
}).reset_index()

# Adicionar área e densidade
ind_mun = ind_mun.merge(municipios[['CD_MUN', 'NM_MUN', 'area_km2']], on='CD_MUN')
ind_mun['densidade_km_km2'] = ind_mun['extensao_km'] / ind_mun['area_km2']

# Salvar indicadores
indicadores = {
    'estado': {
        'extensao_km': float(osm_mun['extensao_km'].sum()),
        'municipios': int(municipios.shape[0]),
        'densidade_media': float(ind_mun['densidade_km_km2'].mean())
    },
    'municipios': ind_mun[['CD_MUN', 'NM_MUN', 'extensao_km', 'densidade_km_km2']].to_dict('records')
}

with open("app_web/data/indicadores.json", 'w', encoding='utf-8') as f:
    json.dump(indicadores, f, ensure_ascii=False, indent=2)

print(f"   ✓ Indicadores salvos")

print("\n" + "="*60)
print("CONCLUÍDO!")
print("="*60)
print(f"\nArquivos criados em app_web/data/:")
print("  - malha_osm.geojson")
print("  - malha_der.geojson")
print("  - municipios_sp.geojson")
print("  - regioes_admin.geojson")
print("  - indicadores.json")
