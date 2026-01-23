"""
Script para adicionar classes de disparidade da Malha Total aos GeoJSONs.
As densidades já estão calculadas, só falta classificar em quintis.
"""
import json
import numpy as np

def calcular_quantis(valores, num_classes=5):
    """Calcula os limites dos quantis para classificação."""
    percentis = np.linspace(0, 100, num_classes + 1)
    return np.percentile(valores, percentis)

def classificar_valor(valor, quantis, classes):
    """Classifica um valor com base nos quantis."""
    if valor is None or np.isnan(valor):
        return None
    for i in range(1, len(quantis)):
        if valor <= quantis[i]:
            return classes[i - 1]
    return classes[-1]

def processar_municipios():
    """Processa o GeoJSON de municípios."""
    print("=== PROCESSANDO MUNICÍPIOS ===")
    
    # Carregar GeoJSON
    with open('municipios_geo_indicadores.geojson', 'r', encoding='utf-8') as f:
        geo = json.load(f)
    
    features = geo['features']
    print(f"Total de municípios: {len(features)}")
    
    # Extrair densidades totais
    dens_area = [f['properties'].get('densidade_total_area_10k') for f in features 
                 if f['properties'].get('densidade_total_area_10k') is not None]
    dens_pop = [f['properties'].get('densidade_total_pop_10k') for f in features 
                if f['properties'].get('densidade_total_pop_10k') is not None]
    
    print(f"Com densidade_total_area_10k: {len(dens_area)}")
    print(f"Com densidade_total_pop_10k: {len(dens_pop)}")
    
    # Calcular quantis
    quantis_area = calcular_quantis(dens_area)
    quantis_pop = calcular_quantis(dens_pop)
    
    classes = ['Muito Abaixo', 'Abaixo', 'Média', 'Acima', 'Muito Acima']
    
    print(f"\nQuantis densidade área: {quantis_area}")
    print(f"Quantis densidade pop: {quantis_pop}")
    
    # Adicionar classes a cada feature
    for f in features:
        props = f['properties']
        dens_a = props.get('densidade_total_area_10k')
        dens_p = props.get('densidade_total_pop_10k')
        
        props['classe_total_disp_area'] = classificar_valor(dens_a, quantis_area, classes)
        props['classe_total_disp_pop'] = classificar_valor(dens_p, quantis_pop, classes)
    
    # Salvar
    with open('municipios_geo_indicadores.geojson', 'w', encoding='utf-8') as f:
        json.dump(geo, f, ensure_ascii=False)
    
    # Contar distribuição
    contagem_area = {}
    contagem_pop = {}
    for f in features:
        ca = f['properties'].get('classe_total_disp_area', 'N/A')
        cp = f['properties'].get('classe_total_disp_pop', 'N/A')
        contagem_area[ca] = contagem_area.get(ca, 0) + 1
        contagem_pop[cp] = contagem_pop.get(cp, 0) + 1
    
    print(f"\nDistribuição classe_total_disp_area: {contagem_area}")
    print(f"Distribuição classe_total_disp_pop: {contagem_pop}")
    print("✓ municipios_geo_indicadores.geojson atualizado!")

def processar_regioes():
    """Processa o GeoJSON de regiões administrativas."""
    print("\n=== PROCESSANDO REGIÕES ADMINISTRATIVAS ===")
    
    # Carregar GeoJSON
    with open('regioes_geo_indicadores.geojson', 'r', encoding='utf-8') as f:
        geo = json.load(f)
    
    features = geo['features']
    print(f"Total de RAs: {len(features)}")
    
    # Verificar propriedades disponíveis
    props_exemplo = features[0]['properties']
    print(f"Propriedades disponíveis: {list(props_exemplo.keys())}")
    
    # Extrair densidades totais (se existirem)
    dens_area = [f['properties'].get('densidade_total_area_10k') for f in features 
                 if f['properties'].get('densidade_total_area_10k') is not None]
    dens_pop = [f['properties'].get('densidade_total_pop_10k') for f in features 
                if f['properties'].get('densidade_total_pop_10k') is not None]
    
    if len(dens_area) == 0:
        print("⚠ Não há densidade_total_area_10k nas RAs. Verificando alternativas...")
        # Verificar se há outras propriedades de densidade
        for k, v in props_exemplo.items():
            if 'dens' in k.lower() or 'total' in k.lower():
                print(f"  → {k}: {v}")
        return
    
    print(f"Com densidade_total_area_10k: {len(dens_area)}")
    print(f"Com densidade_total_pop_10k: {len(dens_pop)}")
    
    # Calcular quantis
    quantis_area = calcular_quantis(dens_area)
    quantis_pop = calcular_quantis(dens_pop)
    
    classes = ['Muito Abaixo', 'Abaixo', 'Média', 'Acima', 'Muito Acima']
    
    print(f"\nQuantis densidade área: {quantis_area}")
    print(f"Quantis densidade pop: {quantis_pop}")
    
    # Adicionar classes a cada feature
    for f in features:
        props = f['properties']
        dens_a = props.get('densidade_total_area_10k')
        dens_p = props.get('densidade_total_pop_10k')
        
        props['classe_total_disp_area'] = classificar_valor(dens_a, quantis_area, classes)
        props['classe_total_disp_pop'] = classificar_valor(dens_p, quantis_pop, classes)
    
    # Salvar
    with open('regioes_geo_indicadores.geojson', 'w', encoding='utf-8') as f:
        json.dump(geo, f, ensure_ascii=False)
    
    print("✓ regioes_geo_indicadores.geojson atualizado!")

if __name__ == '__main__':
    processar_municipios()
    processar_regioes()
    print("\n=== CONCLUÍDO ===")
