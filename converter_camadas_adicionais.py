#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte camadas adicionais para os mapas:
- Malha Rodoviária Estadual DER
- Áreas Urbanizadas IBGE
"""

import geopandas as gpd
import json
from pathlib import Path

print("=" * 80)
print("CONVERSÃO DE CAMADAS ADICIONAIS")
print("=" * 80)

# ============================================================================
# 1. MALHA RODOVIÁRIA ESTADUAL DER
# ============================================================================
print("\n1. MALHA RODOVIÁRIA ESTADUAL (DER)")
print("-" * 80)

estadual_path = Path(r"D:\ESTUDO_VICINAIS_V2\dados\Sistema Rodoviário Estadual\MALHA_RODOVIARIA\MALHA_OUT.shp")

if estadual_path.exists():
    print(f"✓ Lendo: {estadual_path.name}")
    estadual = gpd.read_file(estadual_path)
    
    print(f"  • {len(estadual)} segmentos")
    print(f"  • CRS: {estadual.crs}")
    print(f"  • Tipo: {estadual.geometry.type.unique()}")
    
    # Reprojetar para WGS84
    if estadual.crs and estadual.crs.to_epsg() != 4326:
        print(f"  Reprojetando para WGS84...")
        estadual = estadual.to_crs(epsg=4326)
    
    # Converter datetime
    for col in estadual.columns:
        if estadual[col].dtype in ['datetime64[ns]', 'datetime64[ms]']:
            estadual[col] = estadual[col].astype(str)
    
    # Calcular extensão
    estadual_metric = estadual.to_crs(epsg=31983)
    extensao_km = estadual_metric.geometry.length.sum() / 1000
    print(f"  • Extensão: {extensao_km:,.1f} km")
    
    # Salvar
    output_estadual = Path("app_web/data/malha_estadual_der.geojson")
    output_estadual.parent.mkdir(parents=True, exist_ok=True)
    
    estadual_json = estadual.to_json()
    with open(output_estadual, 'w', encoding='utf-8') as f:
        f.write(estadual_json)
    
    size_estadual = output_estadual.stat().st_size / (1024 * 1024)
    print(f"\n  ✓ Salvo: {output_estadual}")
    print(f"  ✓ Tamanho: {size_estadual:.1f} MB")
else:
    print(f"  ⚠️ Arquivo não encontrado")

# ============================================================================
# 2. ÁREAS URBANIZADAS IBGE
# ============================================================================
print("\n2. ÁREAS URBANIZADAS IBGE")
print("-" * 80)

au_path = Path(r"D:\ESTUDO_VICINAIS_V2\dados\au_ibge.gpkg")

if au_path.exists():
    print(f"✓ Lendo: {au_path.name}")
    au = gpd.read_file(au_path)
    
    print(f"  • {len(au)} áreas urbanizadas")
    print(f"  • CRS: {au.crs}")
    print(f"  • Tipo: {au.geometry.type.unique()}")
    
    # Reprojetar para WGS84
    if au.crs and au.crs.to_epsg() != 4326:
        print(f"  Reprojetando para WGS84...")
        au = au.to_crs(epsg=4326)
    
    # Converter datetime
    for col in au.columns:
        if au[col].dtype in ['datetime64[ns]', 'datetime64[ms]']:
            au[col] = au[col].astype(str)
    
    # Calcular área total
    au_metric = au.to_crs(epsg=31983)
    area_km2 = au_metric.geometry.area.sum() / 1_000_000
    print(f"  • Área total: {area_km2:,.1f} km²")
    
    # Salvar
    output_au = Path("app_web/data/areas_urbanizadas_ibge.geojson")
    
    au_json = au.to_json()
    with open(output_au, 'w', encoding='utf-8') as f:
        f.write(au_json)
    
    size_au = output_au.stat().st_size / (1024 * 1024)
    print(f"\n  ✓ Salvo: {output_au}")
    print(f"  ✓ Tamanho: {size_au:.1f} MB")
else:
    print(f"  ⚠️ Arquivo não encontrado")

print("\n" + "=" * 80)
print("✓ CONVERSÃO CONCLUÍDA")
print("=" * 80)
