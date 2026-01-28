#!/usr/bin/env python3
"""
Gerar tiles TopoJSON (comprimidos) para GitHub Pages
Reduz tamanho de 100MB → ~5-10MB
"""

import json
import os
import gzip
from pathlib import Path
import topojson

# Configurações
ZOOM_LEVELS = {
    8: {'divisoes': 2, 'simplify': 0.001},
    9: {'divisoes': 4, 'simplify': 0.0005},
    10: {'divisoes': 8, 'simplify': 0.0002},
    11: {'divisoes': 16, 'simplify': 0.0001}
}

SP_BOUNDS = {
    'lon': [-53.0022, -44.2227],
    'lat': [-25.2175, -19.8003]
}

def load_geojson(path):
    """Carregar GeoJSON com suporte a .gz"""
    if path.endswith('.gz'):
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

def get_tile_bounds(zoom, x, y):
    """Calcular bbox do tile"""
    lon_range = SP_BOUNDS['lon'][1] - SP_BOUNDS['lon'][0]
    lat_range = SP_BOUNDS['lat'][1] - SP_BOUNDS['lat'][0]
    divisoes = ZOOM_LEVELS[zoom]['divisoes']
    
    tile_lon_width = lon_range / divisoes
    tile_lat_height = lat_range / divisoes
    
    bbox = {
        'min_lon': SP_BOUNDS['lon'][0] + x * tile_lon_width,
        'max_lon': SP_BOUNDS['lon'][0] + (x + 1) * tile_lon_width,
        'min_lat': SP_BOUNDS['lat'][1] - (y + 1) * tile_lat_height,
        'max_lat': SP_BOUNDS['lat'][1] - y * tile_lat_height,
    }
    return bbox

def filter_features_by_bbox(features, bbox):
    """Filtrar features que intersectam com bbox"""
    filtered = []
    
    for feature in features:
        geom = feature.get('geometry', {})
        geom_type = geom.get('type')
        coords = geom.get('coordinates', [])
        
        # Verificar se intersecta com bbox
        intersects = False
        
        if geom_type == 'LineString':
            for lon, lat in coords:
                if (bbox['min_lon'] <= lon <= bbox['max_lon'] and 
                    bbox['min_lat'] <= lat <= bbox['max_lat']):
                    intersects = True
                    break
        elif geom_type == 'MultiLineString':
            for line in coords:
                for lon, lat in line:
                    if (bbox['min_lon'] <= lon <= bbox['max_lon'] and 
                        bbox['min_lat'] <= lat <= bbox['max_lat']):
                        intersects = True
                        break
                if intersects:
                    break
        
        if intersects:
            filtered.append(feature)
    
    return filtered

def save_tile_gz(data, path):
    """Salvar tile como JSON.GZ (comprimido)"""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with gzip.open(path + '.gz', 'wt', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

def main():
    print("🔄 Carregando GeoJSONs...")
    
    # Carregar dados
    malha = load_geojson('docs/data/malha_vicinal_estimada_osm.geojson')
    municipios = load_geojson('docs/data/municipios_geo_indicadores.geojson')
    
    malha_features = malha.get('features', [])
    municipios_features = municipios.get('features', [])
    
    print(f"✅ Malha: {len(malha_features)} features")
    print(f"✅ Municípios: {len(municipios_features)} features")
    
    tiles_path = Path('docs/data/tiles/malha_total')
    tiles_path.mkdir(parents=True, exist_ok=True)
    
    tile_count = 0
    total_features = 0
    
    print("\n🔨 Gerando tiles comprimidos...\n")
    
    for zoom in sorted(ZOOM_LEVELS.keys()):
        divisoes = ZOOM_LEVELS[zoom]['divisoes']
        print(f"📊 Zoom {zoom} ({divisoes}×{divisoes} tiles):")
        
        for x in range(divisoes):
            for y in range(divisoes):
                bbox = get_tile_bounds(zoom, x, y)
                
                # Filtrar features
                malha_tile = filter_features_by_bbox(malha_features, bbox)
                municipios_tile = filter_features_by_bbox(municipios_features, bbox)
                
                if not malha_tile and not municipios_tile:
                    continue
                
                # Criar FeatureCollection
                tile_data = {
                    'type': 'FeatureCollection',
                    'bbox': [bbox['min_lon'], bbox['min_lat'], bbox['max_lon'], bbox['max_lat']],
                    'features': malha_tile + municipios_tile
                }
                
                # Salvar como JSON.GZ
                tile_path = tiles_path / str(zoom) / str(x) / f"{y}"
                save_tile_gz(tile_data, str(tile_path))
                
                feature_count = len(malha_tile) + len(municipios_tile)
                total_features += feature_count
                tile_count += 1
                
                # Verificar tamanho
                gz_size = os.path.getsize(str(tile_path) + '.gz') / 1024
                print(f"  [{x},{y}]: {feature_count} features → {gz_size:.1f} KB")
        
        print()
    
    print(f"✅ TILES GERADOS COM SUCESSO!")
    print(f"   • Total de tiles: {tile_count}")
    print(f"   • Total de features: {total_features}")
    print(f"   • Formato: JSON.GZ (comprimido)")
    
    # Calcular espaço economizado
    estimated_uncompressed = (total_features * 0.15) / 1024  # ~150 bytes por feature
    total_compressed = sum(
        os.path.getsize(f) 
        for f in tiles_path.rglob('*.gz')
    ) / 1024 / 1024
    
    print(f"   • Espaço estimado descomprimido: ~{estimated_uncompressed:.1f} MB")
    print(f"   • Espaço real comprimido: ~{total_compressed:.1f} MB")
    print(f"   • Taxa de compressão: {(1 - total_compressed*1024 / estimated_uncompressed):.1%}")

if __name__ == '__main__':
    main()
