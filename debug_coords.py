import json

with open('docs/data/malha_total_estadual.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

feat = data['features'][0]
coords = feat['geometry']['coordinates']

print(f"Feature type: {feat['geometry']['type']}")
print(f"Coords type: {type(coords)}")
print(f"Coords length: {len(coords)}")
print(f"\nFirst coord: {coords[0]}")
print(f"First coord type: {type(coords[0])}")
print(f"First coord[0]: {coords[0][0]}")
print(f"Type of coords[0][0]: {type(coords[0][0])}")

# Verificar múltiplas features
for i in range(min(3, len(data['features']))):
    f = data['features'][i]
    c = f['geometry']['coordinates']
    print(f"\nFeature {i}: {len(c)} pontos, primeiro={c[0]}")
