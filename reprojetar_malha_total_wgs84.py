"""
Reprojeta malha_total_estadual.geojson de UTM 23S (EPSG:31983) para WGS84 (EPSG:4326)
para uso com Leaflet (que precisa de coordenadas em graus)
"""
import json
from pyproj import Transformer

print("=" * 70)
print("REPROJETANDO MALHA TOTAL: UTM 23S → WGS84")
print("=" * 70)

# Criar transformador de EPSG:31983 (UTM 23S) para EPSG:4326 (WGS84)
print("\n[1/4] Criando transformador de coordenadas...")
transformer = Transformer.from_crs('EPSG:31983', 'EPSG:4326', always_xy=True)
print("      ✓ Transformador criado: EPSG:31983 → EPSG:4326")

# Carregar GeoJSON original
print("\n[2/4] Carregando malha_total_estadual.geojson...")
with open('docs/data/malha_total_estadual.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"      ✓ Carregado: {len(data['features'])} features")

# Reprojetar cada feature
print("\n[3/4] Reprojetando coordenadas...")
features_reprojetadas = 0
pontos_reprojetados = 0

for feature in data['features']:
    geom_type = feature['geometry']['type']
    coords = feature['geometry']['coordinates']
    
    if geom_type == 'LineString':
        # coords = [[x_utm, y_utm], ...]
        novos_coords = []
        for ponto in coords:
            lon, lat = transformer.transform(ponto[0], ponto[1])
            novos_coords.append([lon, lat])
            pontos_reprojetados += 1
        feature['geometry']['coordinates'] = novos_coords
        
    elif geom_type == 'MultiLineString':
        # coords = [[[x_utm, y_utm], ...], ...]
        novos_coords = []
        for linha in coords:
            nova_linha = []
            for ponto in linha:
                lon, lat = transformer.transform(ponto[0], ponto[1])
                nova_linha.append([lon, lat])
                pontos_reprojetados += 1
            novos_coords.append(nova_linha)
        feature['geometry']['coordinates'] = novos_coords
    
    features_reprojetadas += 1
    if features_reprojetadas % 1000 == 0:
        print(f"      → {features_reprojetadas}/{len(data['features'])} features...")

print(f"      ✓ {features_reprojetadas} features reprojetadas")
print(f"      ✓ {pontos_reprojetados} pontos convertidos")

# Salvar novo GeoJSON
print("\n[4/4] Salvando malha_total_estadual_wgs84.geojson...")
with open('docs/data/malha_total_estadual_wgs84.geojson', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

import os
tamanho_mb = os.path.getsize('docs/data/malha_total_estadual_wgs84.geojson') / (1024*1024)
print(f"      ✓ Arquivo salvo: {tamanho_mb:.2f} MB")

print("\n" + "=" * 70)
print("✅ REPROJEÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 70)
print("\nPRÓXIMOS PASSOS:")
print("1. Execute: python gerar_tiles_malha_total.py")
print("   (o script será atualizado para usar o arquivo WGS84)")
print("2. Recarregue a página no navegador")
print("3. As linhas devem aparecer no mapa!")
