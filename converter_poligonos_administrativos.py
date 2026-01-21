#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte polígonos de limites administrativos para GeoJSON
- Municípios de SP
- Regiões Administrativas de SP
"""

import geopandas as gpd
import json
from pathlib import Path

print("=" * 80)
print("CONVERSÃO DE POLÍGONOS ADMINISTRATIVOS")
print("=" * 80)

# ============================================================================
# 1. MUNICÍPIOS
# ============================================================================
print("\n1. MUNICÍPIOS DE SÃO PAULO")
print("-" * 80)

mun_path = Path(r"D:\ESTUDO_VICINAIS_V2\motodologia_abordagem_silvio\Vicinais\Avaliacao_OSM_p_Vicinais\Avaliacao_OSM_p_Vicinais\Div_reg\LimiteMunicipal_SEADE.shp")

if not mun_path.exists():
    print(f"❌ ERRO: {mun_path}")
    exit(1)

print(f"✓ Lendo: {mun_path.name}")
municipios = gpd.read_file(mun_path)

print(f"  • {len(municipios)} municípios")
print(f"  • CRS: {municipios.crs}")
print(f"  • Tipo: {municipios.geometry.type.unique()}")

# Listar colunas
print(f"\n  Colunas disponíveis:")
for col in municipios.columns[:15]:
    if col != 'geometry':
        print(f"    - {col}")

# Reprojetar para WGS84
if municipios.crs and municipios.crs.to_epsg() != 4326:
    print(f"\n  Reprojetando para WGS84...")
    municipios = municipios.to_crs(epsg=4326)

# Converter datetime para string
for col in municipios.columns:
    if municipios[col].dtype in ['datetime64[ns]', 'datetime64[ms]']:
        municipios[col] = municipios[col].astype(str)

# Salvar GeoJSON
output_mun = Path("app_web/data/municipios_sp.geojson")
output_mun.parent.mkdir(parents=True, exist_ok=True)

municipios_json = municipios.to_json()
with open(output_mun, 'w', encoding='utf-8') as f:
    f.write(municipios_json)

size_mun = output_mun.stat().st_size / (1024 * 1024)
print(f"\n  ✓ Salvo: {output_mun}")
print(f"  ✓ Tamanho: {size_mun:.1f} MB")

# ============================================================================
# 2. REGIÕES ADMINISTRATIVAS
# ============================================================================
print("\n2. REGIÕES ADMINISTRATIVAS DE SÃO PAULO")
print("-" * 80)

# Tentar extrair RA dos municípios (dissolver por região administrativa)
if 'RA' in municipios.columns or 'regiao' in municipios.columns or 'REGIAO_ADM' in municipios.columns:
    col_ra = None
    for c in ['RA', 'REGIAO_ADM', 'regiao', 'Regiao', 'REGIAO', 'GID_RA']:
        if c in municipios.columns:
            col_ra = c
            break
    
    if col_ra:
        print(f"  ✓ Coluna de RA encontrada: '{col_ra}'")
        print(f"  • Total de RAs: {municipios[col_ra].nunique()}")
        
        # Dissolver por região administrativa
        print(f"\n  Dissolvendo municípios por RA...")
        regioes = municipios.dissolve(by=col_ra, as_index=False)
        
        print(f"  • {len(regioes)} regiões administrativas")
        
        # Salvar GeoJSON
        output_ra = Path("app_web/data/regioes_administrativas_sp.geojson")
        
        regioes_json = regioes.to_json()
        with open(output_ra, 'w', encoding='utf-8') as f:
            f.write(regioes_json)
        
        size_ra = output_ra.stat().st_size / (1024 * 1024)
        print(f"\n  ✓ Salvo: {output_ra}")
        print(f"  ✓ Tamanho: {size_ra:.1f} MB")
    else:
        print(f"  ⚠️ Coluna de RA não encontrada")
        print(f"  Colunas disponíveis: {list(municipios.columns[:20])}")
else:
    print(f"  ⚠️ Sem coluna de Região Administrativa")

print("\n" + "=" * 80)
print("✓ CONVERSÃO CONCLUÍDA")
print("=" * 80)
print(f"\nArquivos gerados:")
print(f"  • {output_mun}")
if 'output_ra' in locals():
    print(f"  • {output_ra}")
