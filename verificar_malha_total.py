import json

with open('docs/data/malha_total_estadual.geojson', encoding='utf-8') as f:
    data = json.load(f)

print(f"Tipo: {data.get('type')}")
print(f"Features: {len(data.get('features', []))}")

if data.get('features'):
    feat = data['features'][0]
    print(f"\nPrimeira feature:")
    print(f"  Geometria type: {feat.get('geometry', {}).get('type')}")
    print(f"  Propriedades: {feat.get('properties', {})}")
    print(f"  Coords (primeiros 3): {feat.get('geometry', {}).get('coordinates')[:3]}")


