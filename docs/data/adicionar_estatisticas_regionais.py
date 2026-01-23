#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona estatísticas regionais ao arquivo auxiliar_estatisticas_malha.json
Resolve os warnings: "Dados regionais não disponíveis"
"""

import json
import math
from pathlib import Path

def calcular_desvio_padrao(valores):
    """Calcula desvio padrão"""
    if not valores:
        return 0
    media = sum(valores) / len(valores)
    variancia = sum((v - media) ** 2 for v in valores) / len(valores)
    return math.sqrt(variancia)

def calcular_estatisticas(valores):
    """Calcula média, mediana, desvio padrão, mínimo e máximo"""
    if not valores:
        return {"media": 0, "mediana": 0, "desvio_padrao": 0, "minimo": 0, "maximo": 0}
    
    valores_sorted = sorted(valores)
    n = len(valores_sorted)
    media = sum(valores) / n
    mediana = valores_sorted[n // 2] if n % 2 == 1 else (valores_sorted[n//2 - 1] + valores_sorted[n//2]) / 2
    desvio = calcular_desvio_padrao(valores)
    
    return {
        "media": round(media, 4),
        "mediana": round(mediana, 4),
        "desvio_padrao": round(desvio, 4),
        "minimo": round(min(valores), 4),
        "maximo": round(max(valores), 4)
    }

def main():
    data_dir = Path(__file__).parent
    
    # Carregar regiões
    with open(data_dir / 'regioes_indicadores.json', 'r', encoding='utf-8') as f:
        regioes = json.load(f)
    
    print(f"📊 Carregadas {len(regioes)} regiões administrativas")
    
    # Extrair valores para estatísticas OSM
    extensoes_osm = [r.get('extensao_osm_km', r.get('extensao_km', 0)) or 0 for r in regioes]
    dens_area_osm = [r.get('densidade_osm_area_10k', r.get('densidade_area_10k', 0)) or 0 for r in regioes]
    dens_pop_osm = [r.get('densidade_osm_pop_10k', r.get('densidade_pop_10k', 0)) or 0 for r in regioes]
    
    # Extrair valores para estatísticas Total
    extensoes_total = [r.get('extensao_total_km', 0) or 0 for r in regioes]
    dens_area_total = [r.get('densidade_total_area_10k', 0) or 0 for r in regioes]
    dens_pop_total = [r.get('densidade_total_pop_10k', 0) or 0 for r in regioes]
    
    print("\n📈 Calculando estatísticas regionais...")
    
    # Criar seção regional para OSM
    regional_osm = {
        "extensao": calcular_estatisticas(extensoes_osm),
        "densidade_area_10k": calcular_estatisticas(dens_area_osm),
        "densidade_pop_10k": calcular_estatisticas(dens_pop_osm)
    }
    
    # Criar seção regional para Total
    regional_total = {
        "extensao_total": calcular_estatisticas(extensoes_total),
        "densidade_total_area_10k": calcular_estatisticas(dens_area_total),
        "densidade_total_pop_10k": calcular_estatisticas(dens_pop_total)
    }
    
    # Carregar arquivo de estatísticas existente
    stats_file = data_dir / 'auxiliar_estatisticas_malha.json'
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    # Adicionar seção regional
    stats['regional'] = regional_total
    
    # Adicionar desvio padrão às seções municipais se não existirem
    if 'municipal' in stats:
        if 'densidade_total_area_10k' in stats['municipal']:
            if 'desvio_padrao' not in stats['municipal']['densidade_total_area_10k']:
                # Carregar municípios para calcular
                with open(data_dir / 'municipios_indicadores.json', 'r', encoding='utf-8') as f:
                    municipios = json.load(f)
                dens_area_mun = [m.get('densidade_total_area_10k', 0) or 0 for m in municipios]
                stats['municipal']['densidade_total_area_10k']['desvio_padrao'] = round(calcular_desvio_padrao(dens_area_mun), 4)
                
        if 'densidade_total_pop_10k' in stats['municipal']:
            if 'desvio_padrao' not in stats['municipal']['densidade_total_pop_10k']:
                # Carregar municípios para calcular
                with open(data_dir / 'municipios_indicadores.json', 'r', encoding='utf-8') as f:
                    municipios = json.load(f)
                dens_pop_mun = [m.get('densidade_total_pop_10k', 0) or 0 for m in municipios]
                stats['municipal']['densidade_total_pop_10k']['desvio_padrao'] = round(calcular_desvio_padrao(dens_pop_mun), 4)
    
    # Salvar
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Estatísticas adicionadas!")
    print(f"\n📊 Estatísticas Regionais (Total):")
    print(f"   Extensão: média={regional_total['extensao_total']['media']:.2f} km, mediana={regional_total['extensao_total']['mediana']:.2f} km")
    print(f"   Densidade Área: média={regional_total['densidade_total_area_10k']['media']:.2f}, mediana={regional_total['densidade_total_area_10k']['mediana']:.2f}")
    print(f"   Densidade Pop: média={regional_total['densidade_total_pop_10k']['media']:.2f}, mediana={regional_total['densidade_total_pop_10k']['mediana']:.2f}")
    
    print(f"\n✅ Arquivo salvo: {stats_file}")

if __name__ == '__main__':
    main()
