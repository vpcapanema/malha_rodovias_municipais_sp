"""
Script para gerar tiles vetoriais (GeoJSON simplificado) da malha total
SIMPLIFICADO: Divide o estado em grade simples para reduzir carga
"""
import json
import os
from pathlib import Path
import math

def criar_tile_geojson(features_no_tile, z, x, y, output_dir):
    """Cria um tile GeoJSON com as features"""
    tile_path = Path(output_dir) / str(z) / str(x)
    tile_path.mkdir(parents=True, exist_ok=True)
    
    tile_file = tile_path / f"{y}.geojson"
    
    tile_data = {
        "type": "FeatureCollection",
        "features": features_no_tile
    }
    
    with open(tile_file, 'w', encoding='utf-8') as f:
        json.dump(tile_data, f, ensure_ascii=False)
    
    return len(features_no_tile)

def gerar_tiles_simples(geojson_path, output_dir, divisoes=4):
    """
    Gera tiles simples dividindo o estado em grade
    divisoes=4 cria 4x4=16 tiles
    """
    print(f"Carregando {geojson_path}...")
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data['features']
    print(f"Total de features: {len(features)}")
    
    # Calcular bbox (suporta LineString e MultiLineString)
    all_x = []
    all_y = []
    
    for feature in features:
        geom_type = feature['geometry']['type']
        coords = feature['geometry']['coordinates']
        
        if geom_type == 'LineString':
            # coords = [[x,y], [x,y], ...]
            for ponto in coords:
                all_x.append(ponto[0])
                all_y.append(ponto[1])
                
        elif geom_type == 'MultiLineString':
            # coords = [[[x,y], [x,y], ...], [[x,y], [x,y], ...]]
            for linha in coords:
                for ponto in linha:
                    all_x.append(ponto[0])
                    all_y.append(ponto[1])
    
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    print(f"Bbox (WGS84): Lon=[{min_x:.4f}, {max_x:.4f}], Lat=[{min_y:.4f}, {max_y:.4f}]")
    
    # Calcular tamanho de cada tile
    tile_width = (max_x - min_x) / divisoes
    tile_height = (max_y - min_y) / divisoes
    
    print(f"\nCriando grade {divisoes}x{divisoes} tiles...")
    print(f"Tamanho do tile: {tile_width:.4f}° x {tile_height:.4f}°")
    
    zoom = 10  # Zoom fixo para simplificar
    total_tiles = 0
    total_features_escritas = 0
    
    # Para cada célula da grade
    for x_idx in range(divisoes):
        for y_idx in range(divisoes):
            tile_min_x = min_x + (x_idx * tile_width)
            tile_max_x = tile_min_x + tile_width
            tile_min_y = min_y + (y_idx * tile_height)
            tile_max_y = tile_min_y + tile_height
            
            features_no_tile = []
            
            # Filtrar features que intersectam este tile
            for feature in features:
                geom_type = feature['geometry']['type']
                coords = feature['geometry']['coordinates']
                
                intersecta = False
                
                if geom_type == 'LineString':
                    # coords = [[x,y], [x,y], ...]
                    for ponto in coords:
                        x, y = ponto[0], ponto[1]
                        if (tile_min_x <= x <= tile_max_x and 
                            tile_min_y <= y <= tile_max_y):
                            intersecta = True
                            break
                            
                elif geom_type == 'MultiLineString':
                    # coords = [[[x,y], [x,y], ...], [[x,y], [x,y], ...]]
                    for linha in coords:
                        for ponto in linha:
                            x, y = ponto[0], ponto[1]
                            if (tile_min_x <= x <= tile_max_x and 
                                tile_min_y <= y <= tile_max_y):
                                intersecta = True
                                break
                        if intersecta:
                            break
                
                if intersecta:
                    features_no_tile.append(feature)
            
            # Só criar tile se tiver features
            if features_no_tile:
                count = criar_tile_geojson(features_no_tile, zoom, x_idx, y_idx, output_dir)
                total_tiles += 1
                total_features_escritas += count
                print(f"  Tile [{x_idx},{y_idx}]: {count} features")
    
    print(f"\n✅ TILES GERADOS COM SUCESSO!")
    print(f"  Total de tiles: {total_tiles}")
    print(f"  Total de features escritas: {total_features_escritas}")
    print(f"  Diretório: {output_dir}")

if __name__ == "__main__":
    geojson_input = "docs/data/malha_total_estadual_wgs84.geojson"  # Arquivo reprojetado para WGS84
    tiles_output = "docs/data/tiles/malha_total"
    
    print("=" * 60)
    print("GERADOR DE TILES VETORIAIS - MALHA TOTAL (SIMPLIFICADO)")
    print("=" * 60)
    
    gerar_tiles_simples(geojson_input, tiles_output, divisoes=4)
    
    print("\n" + "=" * 60)
    print("PRÓXIMOS PASSOS:")
    print("1. Os tiles GeoJSON estão em docs/data/tiles/malha_total/10/{x}/{y}.geojson")
    print("2. O JavaScript vai carregar apenas os tiles visíveis")
    print("3. Recarregue a página para testar!")
    print("=" * 60)
