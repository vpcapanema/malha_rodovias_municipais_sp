"""
Script para gerar estatísticas de segmentos da malha total (OSM + DER)
Similar ao segmentos_estatisticas.json mas para a malha total
"""
import json
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

def calcular_distribuicao_faixas(gdf):
    """Calcula distribuição de segmentos por faixas de comprimento"""
    comprimentos = gdf.geometry.length / 1000  # Converter para km
    
    faixas = [
        {'faixa': '<1 km', 'min': 0, 'max': 1},
        {'faixa': '1-2 km', 'min': 1, 'max': 2},
        {'faixa': '2-4 km', 'min': 2, 'max': 4},
        {'faixa': '4-6 km', 'min': 4, 'max': 6},
        {'faixa': '6-10 km', 'min': 6, 'max': 10},
        {'faixa': '>10 km', 'min': 10, 'max': float('inf')}
    ]
    
    distribuicao = []
    for f in faixas:
        mask = (comprimentos >= f['min']) & (comprimentos < f['max'])
        segmentos_faixa = comprimentos[mask]
        
        distribuicao.append({
            'faixa': f['faixa'],
            'quantidade': int(mask.sum()),
            'extensao_km': float(segmentos_faixa.sum())
        })
    
    return distribuicao

def calcular_distribuicao_tipo(gdf):
    """Calcula distribuição por tipo de pavimento"""
    # Criar coluna de tipo baseado na origem
    tipos = []
    extensoes = []
    
    # Contar OSM por tipo
    osm_mask = gdf['origem'] == 'OSM_Vicinal'
    if 'surface' in gdf.columns:
        for superficie, nome_amigavel in [
            ('paved', 'Pavimentado'),
            ('asphalt', 'Pavimentado'),
            ('concrete', 'Pavimentado'),
            ('unpaved', 'Não Pavimentado'),
            ('gravel', 'Não Pavimentado'),
            ('dirt', 'Não Pavimentado'),
            ('ground', 'Não Pavimentado'),
            ('compacted', 'Não Pavimentado')
        ]:
            mask = osm_mask & (gdf['surface'] == superficie)
            if mask.sum() > 0:
                ext = gdf[mask].geometry.length.sum() / 1000
                # Adicionar ao tipo existente ou criar novo
                encontrado = False
                for i, t in enumerate(tipos):
                    if t == nome_amigavel:
                        extensoes[i] += ext
                        encontrado = True
                        break
                if not encontrado:
                    tipos.append(nome_amigavel)
                    extensoes.append(ext)
    
    # DER é 100% pavimentado
    der_mask = gdf['origem'] == 'DER_Oficial'
    ext_der = gdf[der_mask].geometry.length.sum() / 1000
    
    # Adicionar DER ao pavimentado
    for i, t in enumerate(tipos):
        if t == 'Pavimentado':
            extensoes[i] += ext_der
            break
    else:
        tipos.append('Pavimentado')
        extensoes.append(ext_der)
    
    return [{'tipo': t, 'extensao_km': e, 'percentual': (e / sum(extensoes)) * 100} 
            for t, e in zip(tipos, extensoes)]

def main():
    base_path = Path(__file__).parent / 'docs' / 'data'
    
    print("📊 Gerando estatísticas de segmentos da malha total...\n")
    
    # Carregar malha total
    print("1️⃣ Carregando malha total...")
    malha_total = gpd.read_file(base_path / 'malha_total_estadual.geojson')
    print(f"   ✓ {len(malha_total):,} segmentos carregados")
    
    # Calcular estatísticas
    print("\n2️⃣ Calculando distribuição por faixas de comprimento...")
    distribuicao_faixas = calcular_distribuicao_faixas(malha_total)
    for d in distribuicao_faixas:
        print(f"   • {d['faixa']}: {d['quantidade']:,} segmentos ({d['extensao_km']:.2f} km)")
    
    print("\n3️⃣ Calculando distribuição por tipo de pavimento...")
    distribuicao_tipo = calcular_distribuicao_tipo(malha_total)
    for d in distribuicao_tipo:
        print(f"   • {d['tipo']}: {d['extensao_km']:.2f} km ({d['percentual']:.1f}%)")
    
    # Calcular estatísticas gerais
    print("\n4️⃣ Calculando estatísticas gerais...")
    comprimentos = malha_total.geometry.length / 1000
    
    estatisticas = {
        'extensao_total_km': float(comprimentos.sum()),
        'total_segmentos': len(malha_total),
        'comprimento_medio_km': float(comprimentos.mean()),
        'comprimento_mediano_km': float(comprimentos.median()),
        'desvio_padrao_km': float(comprimentos.std()),
        'minimo_km': float(comprimentos.min()),
        'maximo_km': float(comprimentos.max())
    }
    
    print(f"   ✓ Extensão total: {estatisticas['extensao_total_km']:,.2f} km")
    print(f"   ✓ Total de segmentos: {estatisticas['total_segmentos']:,}")
    
    # Montar JSON final
    print("\n5️⃣ Montando JSON final...")
    resultado = {
        'estatisticas_segmentos': estatisticas,
        'distribuicao_por_faixas': distribuicao_faixas,
        'distribuicao_por_tipo': distribuicao_tipo
    }
    
    # Salvar
    output_path = base_path / 'segmentos_estatisticas_total.json'
    print(f"\n6️⃣ Salvando {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print("   ✓ Arquivo salvo com sucesso!")
    
    print("\n✅ ESTATÍSTICAS DE SEGMENTOS DA MALHA TOTAL GERADAS!")

if __name__ == '__main__':
    main()
