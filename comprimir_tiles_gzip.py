#!/usr/bin/env python3
"""
Comprimir tiles existentes com gzip
Reduz tamanho dos tiles para usar em GitHub Pages
"""

import json
import os
import gzip
from pathlib import Path

def compress_tiles():
    """Comprimir todos os tiles .geojson com gzip"""
    
    tiles_path = Path('docs/data/tiles/malha_total')
    
    if not tiles_path.exists():
        print("❌ Pasta de tiles não encontrada!")
        return
    
    print("🔄 Comprimindo tiles com gzip...\n")
    
    compressed_count = 0
    original_size = 0
    compressed_size = 0
    
    for geojson_file in sorted(tiles_path.rglob('*.geojson')):
        # Ler arquivo
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Salvar comprimido
        gz_file = geojson_file.with_suffix('.geojson.gz')
        with gzip.open(gz_file, 'wt', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
        
        # Calcular tamanho
        orig_size = os.path.getsize(geojson_file)
        comp_size = os.path.getsize(gz_file)
        compression = (1 - comp_size / orig_size) * 100
        
        original_size += orig_size
        compressed_size += comp_size
        compressed_count += 1
        
        # Exibir info
        tile_path = geojson_file.relative_to(tiles_path)
        print(f"✅ {tile_path}: {orig_size/1024:.1f}KB → {comp_size/1024:.1f}KB ({compression:.1f}%)")
    
    print(f"\n✅ TILES COMPRIMIDOS COM SUCESSO!")
    print(f"   • Total de tiles: {compressed_count}")
    print(f"   • Tamanho original: {original_size/1024/1024:.2f} MB")
    print(f"   • Tamanho comprimido: {compressed_size/1024/1024:.2f} MB")
    print(f"   • Taxa de compressão: {(1 - compressed_size/original_size)*100:.1f}%")
    print(f"   • Economizados: {(original_size - compressed_size)/1024/1024:.2f} MB")

if __name__ == '__main__':
    compress_tiles()
