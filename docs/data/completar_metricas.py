"""
Script para completar as métricas faltantes nos GeoJSONs.

Campos a adicionar/corrigir:

MUNICIPIOS:
- densidade_pop_abs (OSM)
- densidade_total_area_abs (Total)
- densidade_total_pop_abs (Total)
- desvio_total_dens_area (Total)
- desvio_total_dens_pop (Total)
- classe_total_disp_area (recalcular baseado no desvio)
- classe_total_disp_pop (recalcular baseado no desvio)

REGIÕES:
- mesmos campos para a RA
"""
import json

def classificar_por_desvio(desvio):
    """Classifica o município/RA com base no desvio % em relação à média."""
    if desvio is None:
        return None
    if desvio < -50:
        return 'Muito Abaixo'
    elif desvio < -20:
        return 'Abaixo'
    elif desvio <= 20:
        return 'Média'
    elif desvio <= 50:
        return 'Acima'
    else:
        return 'Muito Acima'

def processar_municipios():
    """Processa o GeoJSON de municípios."""
    print("=== PROCESSANDO MUNICÍPIOS ===")
    
    with open('municipios_geo_indicadores.geojson', 'r', encoding='utf-8') as f:
        geo = json.load(f)
    
    features = geo['features']
    print(f"Total de municípios: {len(features)}")
    
    # Calcular médias estaduais para OSM
    extensoes_osm = [f['properties'].get('extensao_km', 0) for f in features]
    areas = [f['properties'].get('Area_Km2', 0) for f in features]
    pops = [f['properties'].get('Pop_2025', 0) for f in features]
    
    # Média estadual OSM: extensão total / área total e extensão total / pop total
    ext_total_osm = sum(extensoes_osm)
    area_total = sum(areas)
    pop_total = sum(pops)
    
    media_dens_area_osm = (ext_total_osm / area_total) * 10000 if area_total > 0 else 0
    media_dens_pop_osm = (ext_total_osm / pop_total) * 10000 if pop_total > 0 else 0
    
    print(f"\nMédia estadual OSM:")
    print(f"  Extensão total: {ext_total_osm:.2f} km")
    print(f"  Área total: {area_total:.2f} km²")
    print(f"  Pop total: {pop_total}")
    print(f"  Densidade área 10k: {media_dens_area_osm:.4f}")
    print(f"  Densidade pop 10k: {media_dens_pop_osm:.4f}")
    
    # Calcular médias estaduais para TOTAL
    extensoes_total = [f['properties'].get('extensao_total_km', 0) for f in features]
    ext_total_total = sum(extensoes_total)
    
    media_dens_area_total = (ext_total_total / area_total) * 10000 if area_total > 0 else 0
    media_dens_pop_total = (ext_total_total / pop_total) * 10000 if pop_total > 0 else 0
    
    print(f"\nMédia estadual TOTAL (OSM + DER):")
    print(f"  Extensão total: {ext_total_total:.2f} km")
    print(f"  Densidade área 10k: {media_dens_area_total:.4f}")
    print(f"  Densidade pop 10k: {media_dens_pop_total:.4f}")
    
    # Processar cada município
    for f in features:
        p = f['properties']
        
        area = p.get('Area_Km2', 0)
        pop = p.get('Pop_2025', 0)
        ext_osm = p.get('extensao_km', 0)
        ext_total = p.get('extensao_total_km', 0)
        
        # 1. densidade_pop_abs (OSM) - faltava
        if pop > 0:
            p['densidade_pop_abs'] = round(ext_osm / pop, 6)
        else:
            p['densidade_pop_abs'] = None
        
        # 2. densidade_total_area_abs
        if area > 0:
            p['densidade_total_area_abs'] = round(ext_total / area, 6)
        else:
            p['densidade_total_area_abs'] = None
        
        # 3. densidade_total_pop_abs
        if pop > 0:
            p['densidade_total_pop_abs'] = round(ext_total / pop, 6)
        else:
            p['densidade_total_pop_abs'] = None
        
        # 4. desvio_total_dens_area
        dens_total_area = p.get('densidade_total_area_10k', 0)
        if media_dens_area_total > 0:
            desvio_area = ((dens_total_area - media_dens_area_total) / media_dens_area_total) * 100
            p['desvio_total_dens_area'] = round(desvio_area, 2)
        else:
            p['desvio_total_dens_area'] = None
        
        # 5. desvio_total_dens_pop
        dens_total_pop = p.get('densidade_total_pop_10k', 0)
        if media_dens_pop_total > 0:
            desvio_pop = ((dens_total_pop - media_dens_pop_total) / media_dens_pop_total) * 100
            p['desvio_total_dens_pop'] = round(desvio_pop, 2)
        else:
            p['desvio_total_dens_pop'] = None
        
        # 6. classe_total_disp_area (baseado no desvio)
        p['classe_total_disp_area'] = classificar_por_desvio(p['desvio_total_dens_area'])
        
        # 7. classe_total_disp_pop (baseado no desvio)
        p['classe_total_disp_pop'] = classificar_por_desvio(p['desvio_total_dens_pop'])
    
    # Salvar
    with open('municipios_geo_indicadores.geojson', 'w', encoding='utf-8') as f:
        json.dump(geo, f, ensure_ascii=False)
    
    # Mostrar distribuição das classes
    print("\nDistribuição classe_total_disp_area:")
    contagem = {}
    for f in features:
        c = f['properties'].get('classe_total_disp_area', 'N/A')
        contagem[c] = contagem.get(c, 0) + 1
    for c in ['Muito Abaixo', 'Abaixo', 'Média', 'Acima', 'Muito Acima']:
        print(f"  {c}: {contagem.get(c, 0)}")
    
    print("\nDistribuição classe_total_disp_pop:")
    contagem = {}
    for f in features:
        c = f['properties'].get('classe_total_disp_pop', 'N/A')
        contagem[c] = contagem.get(c, 0) + 1
    for c in ['Muito Abaixo', 'Abaixo', 'Média', 'Acima', 'Muito Acima']:
        print(f"  {c}: {contagem.get(c, 0)}")
    
    print("\n✓ municipios_geo_indicadores.geojson atualizado!")
    
    # Mostrar exemplo
    print("\nExemplo (Barra do Turvo):")
    for f in features:
        if 'Barra' in str(f['properties'].get('Municipio', '')):
            p = f['properties']
            print(f"  densidade_pop_abs: {p.get('densidade_pop_abs')}")
            print(f"  densidade_total_area_abs: {p.get('densidade_total_area_abs')}")
            print(f"  densidade_total_pop_abs: {p.get('densidade_total_pop_abs')}")
            print(f"  desvio_total_dens_area: {p.get('desvio_total_dens_area')}%")
            print(f"  desvio_total_dens_pop: {p.get('desvio_total_dens_pop')}%")
            print(f"  classe_total_disp_area: {p.get('classe_total_disp_area')}")
            print(f"  classe_total_disp_pop: {p.get('classe_total_disp_pop')}")
            break

def processar_regioes():
    """Processa o GeoJSON de regiões administrativas."""
    print("\n=== PROCESSANDO REGIÕES ADMINISTRATIVAS ===")
    
    with open('regioes_geo_indicadores.geojson', 'r', encoding='utf-8') as f:
        geo = json.load(f)
    
    features = geo['features']
    print(f"Total de RAs: {len(features)}")
    
    # Calcular médias estaduais para TOTAL (usando dados das RAs)
    extensoes_total = [f['properties'].get('extensao_total_km', 0) for f in features]
    areas = [f['properties'].get('area_km2', 0) for f in features]
    pops = [f['properties'].get('populacao', 0) for f in features]
    
    ext_total = sum(extensoes_total)
    area_total = sum(areas)
    pop_total = sum(pops)
    
    media_dens_area_total = (ext_total / area_total) * 10000 if area_total > 0 else 0
    media_dens_pop_total = (ext_total / pop_total) * 10000 if pop_total > 0 else 0
    
    print(f"\nMédia estadual TOTAL (RA):")
    print(f"  Extensão total: {ext_total:.2f} km")
    print(f"  Área total: {area_total:.2f} km²")
    print(f"  Pop total: {pop_total}")
    print(f"  Densidade área 10k: {media_dens_area_total:.4f}")
    print(f"  Densidade pop 10k: {media_dens_pop_total:.4f}")
    
    # Processar cada RA
    for f in features:
        p = f['properties']
        
        area = p.get('area_km2', 0)
        pop = p.get('populacao', 0)
        ext_osm = p.get('extensao_osm_km', p.get('extensao_km', 0))
        ext_total = p.get('extensao_total_km', 0)
        
        # densidade_pop_abs (OSM)
        if pop > 0:
            p['densidade_pop_abs'] = round(ext_osm / pop, 6)
        else:
            p['densidade_pop_abs'] = None
        
        # densidade_total_area_abs
        if area > 0:
            p['densidade_total_area_abs'] = round(ext_total / area, 6)
        else:
            p['densidade_total_area_abs'] = None
        
        # densidade_total_pop_abs
        if pop > 0:
            p['densidade_total_pop_abs'] = round(ext_total / pop, 6)
        else:
            p['densidade_total_pop_abs'] = None
        
        # desvio_total_dens_area
        dens_total_area = p.get('densidade_total_area_10k', 0)
        if media_dens_area_total > 0:
            desvio_area = ((dens_total_area - media_dens_area_total) / media_dens_area_total) * 100
            p['desvio_total_dens_area'] = round(desvio_area, 2)
        else:
            p['desvio_total_dens_area'] = None
        
        # desvio_total_dens_pop
        dens_total_pop = p.get('densidade_total_pop_10k', 0)
        if media_dens_pop_total > 0:
            desvio_pop = ((dens_total_pop - media_dens_pop_total) / media_dens_pop_total) * 100
            p['desvio_total_dens_pop'] = round(desvio_pop, 2)
        else:
            p['desvio_total_dens_pop'] = None
        
        # classe_total_disp_area
        p['classe_total_disp_area'] = classificar_por_desvio(p['desvio_total_dens_area'])
        
        # classe_total_disp_pop
        p['classe_total_disp_pop'] = classificar_por_desvio(p['desvio_total_dens_pop'])
    
    # Salvar
    with open('regioes_geo_indicadores.geojson', 'w', encoding='utf-8') as f:
        json.dump(geo, f, ensure_ascii=False)
    
    print("\n✓ regioes_geo_indicadores.geojson atualizado!")
    
    # Mostrar exemplo
    print("\nExemplo (primeira RA):")
    p = features[0]['properties']
    print(f"  RA: {p.get('RA')}")
    print(f"  densidade_pop_abs: {p.get('densidade_pop_abs')}")
    print(f"  densidade_total_area_abs: {p.get('densidade_total_area_abs')}")
    print(f"  densidade_total_pop_abs: {p.get('densidade_total_pop_abs')}")
    print(f"  desvio_total_dens_area: {p.get('desvio_total_dens_area')}%")
    print(f"  desvio_total_dens_pop: {p.get('desvio_total_dens_pop')}%")
    print(f"  classe_total_disp_area: {p.get('classe_total_disp_area')}")
    print(f"  classe_total_disp_pop: {p.get('classe_total_disp_pop')}")

if __name__ == '__main__':
    processar_municipios()
    processar_regioes()
    print("\n=== CONCLUÍDO ===")
