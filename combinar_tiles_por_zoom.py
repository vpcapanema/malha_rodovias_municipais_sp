#!/usr/bin/env python3
"""
Combinar tiles por zoom level em um único arquivo comprimido
Reduz de 14 arquivos para 4 + metadata
"""

import json
import gzip
from pathlib import Path

def combine_tiles_by_zoom():
    tiles_path = Path('docs/data/tiles/malha_total')
    output_path = Path('docs/data/tiles')
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("🔄 Combinando tiles por zoom level...\n")
    
    for zoom in [8, 9, 10, 11]:
        print(f"📦 Zoom {zoom}:")
        
        tiles_by_zoom = {}
        total_features = 0
        
        # Coletar todos os tiles deste zoom
        zoom_path = tiles_path / str(zoom)
        if not zoom_path.exists():
            print(f"   ⚠️ Nenhum tile encontrado para zoom {zoom}")
            continue
        
        for geojson_file in sorted(zoom_path.rglob('*.geojson')):
            with open(geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            tile_coords = f"{geojson_file.parent.name}/{geojson_file.stem}"
            tiles_by_zoom[tile_coords] = features
            total_features += len(features)
        
        # Salvar como arquivo único comprimido
        combined = {
            'zoom': zoom,
            'tiles': tiles_by_zoom,
            'total_features': total_features
        }
        
        output_file = output_path / f"tiles_z{zoom}.json.gz"
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            json.dump(combined, f, separators=(',', ':'))
        
        file_size = output_file.stat().st_size / 1024 / 1024
        print(f"   ✅ {len(tiles_by_zoom)} tiles → {file_size:.2f} MB")
    
    print("\n✅ TILES AGRUPADOS COM SUCESSO!")

if __name__ == '__main__':
    combine_tiles_by_zoom()
