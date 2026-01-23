import json

# Carregar GeoJSON e métricas
with open('docs/data/municipios_sp.geojson', 'r', encoding='utf-8') as f:
    geo_data = json.load(f)

with open('docs/data/municipios_indicadores_total.json', 'r', encoding='utf-8') as f:
    metricas_data = json.load(f)

print("🔍 COMPARAÇÃO DE CÓDIGOS IBGE")
print("=" * 60)

# Primeiro município do GeoJSON
geo_cod = geo_data['features'][0]['properties']['Cod_ibge']
print(f"\nGeoJSON - Primeiro município:")
print(f"  Cod_ibge: '{geo_cod}' (tipo: {type(geo_cod).__name__})")

# Primeiro município das métricas
met_cod = metricas_data[0]['Cod_ibge']
print(f"\nMétricas - Primeiro município:")
print(f"  Cod_ibge: '{met_cod}' (tipo: {type(met_cod).__name__})")

# Comparação
print(f"\nComparação:")
print(f"  Iguais: {geo_cod == met_cod}")
print(f"  GeoJSON convertido para string: '{str(geo_cod)}'")
print(f"  Métricas convertido para int: {int(met_cod) if isinstance(met_cod, str) else met_cod}")

# Verificar todos os códigos
geo_codigos = {f['properties']['Cod_ibge'] for f in geo_data['features']}
met_codigos = {m['Cod_ibge'] for m in metricas_data}

print(f"\n📊 ESTATÍSTICAS:")
print(f"  GeoJSON tem {len(geo_codigos)} códigos únicos")
print(f"  Métricas tem {len(met_codigos)} códigos únicos")
print(f"  Match: {len(geo_codigos & met_codigos)} códigos em comum")

# Mostrar exemplo de códigos não matched
nao_matched_geo = list(geo_codigos - met_codigos)[:3]
nao_matched_met = list(met_codigos - geo_codigos)[:3]

print(f"\n❌ Exemplos não matched:")
if nao_matched_geo:
    print(f"  GeoJSON sem métrica: {nao_matched_geo}")
if nao_matched_met:
    print(f"  Métricas sem GeoJSON: {nao_matched_met}")
