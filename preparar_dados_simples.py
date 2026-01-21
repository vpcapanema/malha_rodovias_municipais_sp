import geopandas as gpd
import json
import os

print("="*60)
print("PREPARANDO DADOS SIMPLIFICADOS")
print("="*60)

os.makedirs("app_web/data", exist_ok=True)

# ============================================================================
# 1. MALHA OSM (SEM SIMPLIFICAÇÃO - GEOMETRIA ORIGINAL)
# ============================================================================
print("\n1. Malha OSM...")
osm = gpd.read_file("dados/vicinais_sp.gpkg")

# Calcular estatísticas por highway
stats_tipo = osm.groupby('highway')['comprimento_m'].agg(['count', 'sum']).reset_index()
stats_tipo['km_total'] = stats_tipo['sum'] / 1000
print(f"   Total: {len(osm):,} segmentos | {osm['comprimento_m'].sum()/1000:.0f} km")

# Salvar SEM simplificação
osm_json = osm.to_json()
with open("app_web/data/malha_osm.geojson", 'w') as f:
    f.write(osm_json)
print(f"   ✓ Salvo (original completo): {len(osm_json)/1024/1024:.1f} MB")

# ============================================================================
# 2. MALHA DER (SEM SIMPLIFICAÇÃO - GEOMETRIA ORIGINAL)
# ============================================================================
print("\n2. Malha DER...")
try:
    der = gpd.read_file("dados/vicinais_simples.gpkg")
    print(f"   Colunas: {der.columns.tolist()}")
    print(f"   Total: {len(der):,} segmentos")
    
    # Calcular comprimento se não existir
    if 'comprimento_m' not in der.columns:
        der_calc = der.to_crs(epsg=31983)  # SIRGAS 2000 / UTM zone 23S
        der['comprimento_m'] = der_calc.geometry.length
    
    total_km = der['comprimento_m'].sum() / 1000 if 'comprimento_m' in der.columns else 0
    print(f"   Extensão total: {total_km:.0f} km")
    
    # Salvar SEM simplificação
    der_json = der.to_json()
    with open("app_web/data/malha_der.geojson", 'w') as f:
        f.write(der_json)
    print(f"   ✓ Salvo (original completo): {len(der_json)/1024/1024:.1f} MB")
    
except Exception as e:
    print(f"   ✗ Erro: {e}")

# ============================================================================
# 3. INDICADORES GLOBAIS
# ============================================================================
print("\n3. Indicadores...")
indicadores = {
    'osm': {
        'segmentos': int(len(osm)),
        'extensao_km': float(osm['comprimento_m'].sum() / 1000),
        'por_tipo': stats_tipo.to_dict('records')
    },
    'der': {
        'segmentos': int(len(der)) if 'der' in locals() else 0,
        'extensao_km': float(total_km) if 'total_km' in locals() else 0
    }
}

with open("app_web/data/indicadores.json", 'w') as f:
    json.dump(indicadores, f, indent=2)

print(f"   ✓ Indicadores salvos")

print("\n" + "="*60)
print("CONCLUÍDO!")
print("="*60)
print(f"\nResumo:")
print(f"  OSM: {indicadores['osm']['extensao_km']:,.0f} km em {indicadores['osm']['segmentos']:,} segmentos")
print(f"  DER: {indicadores['der']['extensao_km']:,.0f} km em {indicadores['der']['segmentos']:,} segmentos")
