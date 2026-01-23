"""
Script para gerar estatísticas completas da malha total (OSM + DER)
incluindo segmentos e distribuições municipais
"""
import json
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

def calcular_estatisticas_segmentos(gdf):
    """Calcula estatísticas dos segmentos"""
    comprimentos = gdf.geometry.length / 1000  # Converter para km
    
    return {
        'comprimento_medio_km': float(comprimentos.mean()),
        'comprimento_mediano_km': float(comprimentos.median()),
        'desvio_padrao_km': float(comprimentos.std()),
        'minimo_km': float(comprimentos.min()),
        'maximo_km': float(comprimentos.max())
    }

def calcular_estatisticas_municipal(dados_municipios, campo_extensao):
    """Calcula estatísticas da distribuição municipal"""
    extensoes = dados_municipios[campo_extensao]
    
    return {
        'media': float(extensoes.mean()),
        'mediana': float(extensoes.median()),
        'desvio_padrao': float(extensoes.std()),
        'minimo': float(extensoes.min()),
        'maximo': float(extensoes.max())
    }

def calcular_estatisticas_densidade(dados_municipios, campo_densidade):
    """Calcula estatísticas de densidade"""
    densidades = dados_municipios[campo_densidade]
    
    return {
        'media': float(densidades.mean()),
        'mediana': float(densidades.median()),
        'minimo': float(densidades.min()),
        'maximo': float(densidades.max())
    }

def main():
    base_path = Path(__file__).parent / 'docs' / 'data'
    
    print("📊 Gerando estatísticas completas da malha total...\n")
    
    # 1. Carregar malha total
    print("1️⃣ Carregando malha total...")
    malha_total = gpd.read_file(base_path / 'malha_total_estadual.geojson')
    print(f"   ✓ {len(malha_total):,} segmentos carregados")
    
    # 2. Carregar indicadores municipais da malha total
    print("\n2️⃣ Carregando indicadores municipais...")
    with open(base_path / 'municipios_indicadores_total.json', 'r', encoding='utf-8') as f:
        municipios_total = pd.DataFrame(json.load(f))
    print(f"   ✓ {len(municipios_total):,} municípios carregados")
    
    # 3. Calcular estatísticas dos segmentos
    print("\n3️⃣ Calculando estatísticas dos segmentos...")
    stats_segmentos = calcular_estatisticas_segmentos(malha_total)
    print(f"   ✓ Comprimento médio: {stats_segmentos['comprimento_medio_km']:.2f} km")
    print(f"   ✓ Comprimento mediano: {stats_segmentos['comprimento_mediano_km']:.2f} km")
    
    # 4. Calcular estatísticas municipais
    print("\n4️⃣ Calculando estatísticas municipais...")
    stats_extensao = calcular_estatisticas_municipal(municipios_total, 'extensao_total_km')
    print(f"   ✓ Extensão média municipal: {stats_extensao['media']:.2f} km")
    print(f"   ✓ Extensão mediana municipal: {stats_extensao['mediana']:.2f} km")
    
    # 5. Calcular estatísticas de densidade área
    print("\n5️⃣ Calculando estatísticas de densidade área...")
    stats_dens_area = calcular_estatisticas_densidade(municipios_total, 'densidade_total_area_10k')
    print(f"   ✓ Densidade média: {stats_dens_area['media']:.2f} km/10k km²")
    
    # 6. Calcular estatísticas de densidade populacional
    print("\n6️⃣ Calculando estatísticas de densidade populacional...")
    stats_dens_pop = calcular_estatisticas_densidade(municipios_total, 'densidade_total_pop_10k')
    print(f"   ✓ Densidade média: {stats_dens_pop['media']:.2f} km/10k hab")
    
    # 7. Montar estrutura completa
    print("\n7️⃣ Montando estrutura JSON completa...")
    estatisticas_completas = {
        'malha_total': {
            'extensao_total_km': float(malha_total.geometry.length.sum() / 1000),
            'num_segmentos_total': len(malha_total),
            'num_municipios': len(municipios_total)
        },
        'segmentos': stats_segmentos,
        'municipal': {
            'extensao_total': stats_extensao,
            'densidade_total_area_10k': stats_dens_area,
            'densidade_total_pop_10k': stats_dens_pop
        }
    }
    
    # 8. Salvar JSON
    output_path = base_path / 'estatisticas_malha_total.json'
    print(f"\n8️⃣ Salvando {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(estatisticas_completas, f, indent=2, ensure_ascii=False)
    print("   ✓ Arquivo salvo com sucesso!")
    
    print("\n✅ ESTATÍSTICAS COMPLETAS GERADAS!")
    print(f"\n📋 Resumo:")
    print(f"   • Malha Total: {estatisticas_completas['malha_total']['extensao_total_km']:,.2f} km")
    print(f"   • Segmentos: {estatisticas_completas['malha_total']['num_segmentos_total']:,}")
    print(f"   • Municípios: {estatisticas_completas['malha_total']['num_municipios']:,}")
    print(f"   • Comprimento médio: {stats_segmentos['comprimento_medio_km']:.2f} km")
    print(f"   • Extensão média municipal: {stats_extensao['media']:.2f} km")
    print(f"   • Densidade espacial média: {stats_dens_area['media']:.2f} km/10k km²")
    print(f"   • Densidade populacional média: {stats_dens_pop['media']:.2f} km/10k hab")

if __name__ == '__main__':
    main()
