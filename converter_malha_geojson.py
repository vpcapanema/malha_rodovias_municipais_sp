import geopandas as gpd
import json

# Carregar a malha vicinal completa
print("Carregando vicinais_sp.gpkg...")
vicinais = gpd.read_file("dados/vicinais_sp.gpkg")

print(f"Total de segmentos: {len(vicinais)}")
print(f"Colunas disponíveis: {vicinais.columns.tolist()}")

# Simplificar geometria para reduzir tamanho
vicinais_simple = vicinais.copy()
vicinais_simple['geometry'] = vicinais_simple.geometry.simplify(0.001, preserve_topology=True)

# Converter para GeoJSON
geojson = vicinais_simple.to_json()

# Salvar
output_path = "app_web/data/malha_vicinais.geojson"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(geojson)

print(f"✓ GeoJSON salvo em {output_path}")
print(f"  Tamanho: {len(geojson) / 1024 / 1024:.2f} MB")
