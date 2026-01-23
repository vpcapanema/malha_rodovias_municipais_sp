#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera arquivo GeoJSON consolidado com geometrias + todas as métricas (OSM + Total)

Combina:
- docs/data/municipios_sp.geojson (geometrias)
- docs/data/municipios_indicadores_total.json (métricas OSM + Total)

Saída:
- docs/data/municipios_completo.geojson (geometria + todas métricas)
"""

import json
from pathlib import Path

def main():
    print("=" * 60)
    print("GERAÇÃO DE GEOJSON COMPLETO DE MUNICÍPIOS")
    print("=" * 60)
    
    # Caminhos
    base_dir = Path(__file__).parent
    docs_data = base_dir / "docs" / "data"
    
    geojson_path = docs_data / "municipios_sp.geojson"
    metricas_path = docs_data / "municipios_indicadores_total.json"
    output_path = docs_data / "municipios_completo.geojson"
    
    # 1. Carregar GeoJSON com geometrias
    print(f"\n[1/4] Carregando geometrias: {geojson_path.name}")
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    print(f"   ✓ {len(geojson['features'])} municípios carregados")
    
    # 2. Carregar métricas (OSM + Total)
    print(f"\n[2/4] Carregando métricas: {metricas_path.name}")
    with open(metricas_path, 'r', encoding='utf-8') as f:
        metricas = json.load(f)
    
    print(f"   ✓ {len(metricas)} registros de métricas carregados")
    
    # 3. Criar mapa de métricas por código IBGE (converter string para int para match com GeoJSON)
    print("\n[3/4] Mesclando dados...")
    metricas_map = {int(m['Cod_ibge']): m for m in metricas}
    
    municipios_sem_metrica = 0
    metricas_nao_usadas = set(metricas_map.keys())
    
    # Mesclar métricas nas features
    for feature in geojson['features']:
        props = feature['properties']
        # Campo correto verificado: 'Cod_ibge'
        cod_ibge = props.get('Cod_ibge')
        
        if cod_ibge and cod_ibge in metricas_map:
            # Adicionar todas as métricas
            metrica = metricas_map[cod_ibge]
            props.update(metrica)
            metricas_nao_usadas.discard(cod_ibge)
        else:
            municipios_sem_metrica += 1
            print(f"   ⚠️  Município sem métrica: {props.get('NM_MUN', 'N/A')} ({cod_ibge})")
    
    print(f"   ✓ Mesclagem concluída")
    print(f"   → Municípios com métricas: {len(geojson['features']) - municipios_sem_metrica}")
    print(f"   → Municípios sem métricas: {municipios_sem_metrica}")
    
    if metricas_nao_usadas:
        print(f"   ⚠️  Métricas não usadas: {len(metricas_nao_usadas)}")
    
    # 4. Salvar arquivo completo
    print(f"\n[4/4] Salvando: {output_path.name}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(',', ':'))
    
    # Estatísticas de tamanho
    tamanho_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"   ✓ Arquivo salvo com sucesso!")
    print(f"   → Tamanho: {tamanho_mb:.2f} MB")
    
    # Verificar propriedades disponíveis (amostra do primeiro município)
    if geojson['features']:
        props_exemplo = geojson['features'][0]['properties']
        print(f"\n📊 PROPRIEDADES DISPONÍVEIS ({len(props_exemplo)} campos):")
        print("\n   Básicas:")
        for key in ['CD_MUN', 'NM_MUN', 'Cod_ibge', 'Municipio', 'RA', 'Area_Km2', 'Pop_2025']:
            if key in props_exemplo:
                print(f"      - {key}")
        
        print("\n   Malha OSM:")
        for key in ['extensao_km', 'densidade_area_10k', 'densidade_pop_10k', 
                    'desvio_dens_area', 'desvio_dens_pop', 
                    'classe_disp_area', 'classe_disp_pop']:
            if key in props_exemplo:
                print(f"      - {key}")
        
        print("\n   Malha Total (OSM + DER):")
        for key in ['extensao_total_km', 'densidade_total_area_10k', 'densidade_total_pop_10k',
                    'densidade_total_area_abs', 'desvio_total_dens_area', 'desvio_total_dens_pop',
                    'classe_total_disp_area', 'classe_total_disp_pop']:
            if key in props_exemplo:
                print(f"      - {key}")
    
    print("\n" + "=" * 60)
    print("✅ GEOJSON COMPLETO GERADO COM SUCESSO!")
    print("=" * 60)
    print(f"\nArquivo: {output_path}")
    print(f"Features: {len(geojson['features'])}")
    print(f"Tamanho: {tamanho_mb:.2f} MB")
    print("\nPróximo passo: Atualizar JavaScript para usar municipios_completo.geojson")

if __name__ == '__main__':
    main()
