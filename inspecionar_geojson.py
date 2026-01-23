import json

# Carregar apenas a primeira feature do GeoJSON
with open('docs/data/municipios_sp.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

first_feature = data['features'][0]
print("🔍 PROPRIEDADES DA PRIMEIRA FEATURE:")
print("=" * 60)
for key, value in first_feature['properties'].items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print(f"✅ Total de propriedades: {len(first_feature['properties'])}")
print(f"✅ Total de features no arquivo: {len(data['features'])}")
