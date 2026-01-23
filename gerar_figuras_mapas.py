"""
Script para gerar figuras de mapas temáticos para o relatório técnico
Gera mapas das malhas e indicadores municipais/regionais
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import json
import numpy as np
from pathlib import Path

# Configurações
OUTPUT_DIR = Path(r"D:\ESTUDO_VICINAIS_V2\motodologia_abordagem_silvio\Vicinais\Figuras\Figuras")
DATA_DIR = Path(r"D:\ESTUDO_VICINAIS_V2\docs\data")

# Estilo consistente
plt.style.use('seaborn-v0_8-darkgrid')
FIGSIZE = (16, 12)
DPI = 300

def configurar_mapa_base(ax, titulo, subtitulo=""):
    """Configura elementos básicos do mapa"""
    ax.set_title(titulo, fontsize=18, fontweight='bold', pad=20)
    if subtitulo:
        ax.text(0.5, 1.02, subtitulo, transform=ax.transAxes, 
                ha='center', fontsize=12, style='italic')
    ax.axis('off')
    
    # Adicionar indicação de escala (texto simples)
    ax.text(0.02, 0.02, '0 ─────── 100 km', transform=ax.transAxes,
           fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Adicionar seta norte
    x, y, arrow_length = 0.95, 0.95, 0.08
    ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
                arrowprops=dict(facecolor='black', width=3, headwidth=10),
                ha='center', va='center', fontsize=14, fontweight='bold',
                xycoords=ax.transAxes)

def criar_legenda_quantis(valores, cmap_name, n_classes=5):
    """Cria classificação por quantis"""
    valores_limpos = valores[~np.isnan(valores)]
    quantiles = np.percentile(valores_limpos, np.linspace(0, 100, n_classes + 1))
    return quantiles

def formatar_numero(valor):
    """Formata números para legenda"""
    if valor >= 1000:
        return f"{valor/1000:.1f}k"
    elif valor >= 100:
        return f"{valor:.0f}"
    else:
        return f"{valor:.1f}"

# =============================================================================
# MAPA 1: MALHA VICINAL ESTIMADA (OSM)
# =============================================================================
def gerar_mapa_malha_vicinal():
    print("\n[1/7] Gerando mapa da malha vicinal estimada...")
    
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE, dpi=DPI)
    
    # Carregar dados
    municipios = gpd.read_file(DATA_DIR / "municipios_geo_indicadores.geojson")
    malha_vicinal = gpd.read_file(DATA_DIR / "malha_vicinal_estimada_osm.geojson")
    
    # Plotar
    municipios.plot(ax=ax, color='#f0f0f0', edgecolor='#666666', linewidth=0.5, alpha=0.6)
    malha_vicinal.plot(ax=ax, color='#e74c3c', linewidth=0.8, alpha=0.8)
    
    configurar_mapa_base(ax, 
                        "Malha Vicinal Estimada - Estado de São Paulo",
                        "Base: OpenStreetMap | Processamento: PLI/SP")
    
    # Legenda
    legend_elements = [
        Line2D([0], [0], color='#e74c3c', linewidth=2, label='Vicinais (OSM)'),
        mpatches.Patch(facecolor='#f0f0f0', edgecolor='#666666', label='Municípios')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11, framealpha=0.9)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "mapa_malha_vicinal_osm.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✓ Salvo: {output_path.name}")

# =============================================================================
# MAPA 2: MALHA ESTADUAL (DER)
# =============================================================================
def gerar_mapa_malha_der():
    print("\n[2/7] Gerando mapa da malha estadual (DER)...")
    
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE, dpi=DPI)
    
    # Carregar dados
    municipios = gpd.read_file(DATA_DIR / "municipios_geo_indicadores.geojson")
    malha_der = gpd.read_file(DATA_DIR / "malha_estadual_federal_der.geojson")
    
    # Plotar
    municipios.plot(ax=ax, color='#f0f0f0', edgecolor='#666666', linewidth=0.5, alpha=0.6)
    malha_der.plot(ax=ax, color='#3498db', linewidth=1.2, alpha=0.8)
    
    configurar_mapa_base(ax, 
                        "Malha Estadual e Federal - Estado de São Paulo",
                        "Base: DER/SP | Sistema: SIRGAS 2000 / UTM 23S")
    
    # Legenda
    legend_elements = [
        Line2D([0], [0], color='#3498db', linewidth=2, label='Estadual/Federal (DER)'),
        mpatches.Patch(facecolor='#f0f0f0', edgecolor='#666666', label='Municípios')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11, framealpha=0.9)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "mapa_malha_estadual_der.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✓ Salvo: {output_path.name}")

# =============================================================================
# MAPA 3: MALHA COMPLETA (VICINAL + DER)
# =============================================================================
def gerar_mapa_malha_completa():
    print("\n[3/7] Gerando mapa da malha completa...")
    
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE, dpi=DPI)
    
    # Carregar dados
    municipios = gpd.read_file(DATA_DIR / "municipios_geo_indicadores.geojson")
    malha_completa = gpd.read_file(DATA_DIR / "malha_vicinal_estimada_com_der.geojson")
    
    # Plotar
    municipios.plot(ax=ax, color='#f0f0f0', edgecolor='#666666', linewidth=0.5, alpha=0.6)
    malha_completa.plot(ax=ax, color='#9b59b6', linewidth=0.7, alpha=0.7)
    
    configurar_mapa_base(ax, 
                        "Malha Rodoviária Completa - Estado de São Paulo",
                        "Base: OSM + DER/SP | Malha Vicinal + Estadual/Federal")
    
    # Legenda
    legend_elements = [
        Line2D([0], [0], color='#9b59b6', linewidth=2, label='Malha Completa'),
        mpatches.Patch(facecolor='#f0f0f0', edgecolor='#666666', label='Municípios')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11, framealpha=0.9)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "mapa_malha_completa.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✓ Salvo: {output_path.name}")

# =============================================================================
# MAPA 4: DENSIDADE ESPACIAL MUNICIPAL
# =============================================================================
def gerar_mapa_densidade_espacial_municipal():
    print("\n[4/7] Gerando mapa de densidade espacial municipal...")
    
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE, dpi=DPI)
    
    # Carregar dados
    municipios = gpd.read_file(DATA_DIR / "municipios_geo_indicadores.geojson")
    
    # Classificação por quantis
    valores = municipios['densidade_area_10k'].values
    breaks = criar_legenda_quantis(valores, 'Reds', n_classes=5)
    
    # Plotar
    municipios.plot(column='densidade_area_10k', ax=ax, 
                   cmap='Reds', edgecolor='#333333', linewidth=0.3,
                   legend=False, scheme='User_Defined',
                   classification_kwds={'bins': breaks})
    
    configurar_mapa_base(ax, 
                        "Densidade de Malha Vicinal por Área - Escala Municipal",
                        "Indicador: km de vicinais / 10.000 km² | Classificação: Quantis")
    
    # Legenda customizada
    labels = []
    for i in range(len(breaks) - 1):
        labels.append(f"{formatar_numero(breaks[i])} - {formatar_numero(breaks[i+1])}")
    
    colors = plt.cm.Reds(np.linspace(0.3, 1, len(breaks)-1))
    legend_elements = [mpatches.Patch(facecolor=colors[i], edgecolor='black', 
                                     label=labels[i]) for i in range(len(labels))]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             title='km / 10.000 km²', fontsize=10, framealpha=0.9)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "mapa_densidade_espacial_municipal.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✓ Salvo: {output_path.name}")

# =============================================================================
# MAPA 5: DENSIDADE POPULACIONAL MUNICIPAL
# =============================================================================
def gerar_mapa_densidade_populacional_municipal():
    print("\n[5/7] Gerando mapa de densidade populacional municipal...")
    
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE, dpi=DPI)
    
    # Carregar dados
    municipios = gpd.read_file(DATA_DIR / "municipios_geo_indicadores.geojson")
    
    # Classificação por quantis
    valores = municipios['densidade_pop_10k'].values
    breaks = criar_legenda_quantis(valores, 'Oranges', n_classes=5)
    
    # Plotar
    municipios.plot(column='densidade_pop_10k', ax=ax, 
                   cmap='Oranges', edgecolor='#333333', linewidth=0.3,
                   legend=False, scheme='User_Defined',
                   classification_kwds={'bins': breaks})
    
    configurar_mapa_base(ax, 
                        "Densidade de Malha Vicinal por População - Escala Municipal",
                        "Indicador: km de vicinais / 10.000 habitantes | Classificação: Quantis")
    
    # Legenda customizada
    labels = []
    for i in range(len(breaks) - 1):
        labels.append(f"{formatar_numero(breaks[i])} - {formatar_numero(breaks[i+1])}")
    
    colors = plt.cm.Oranges(np.linspace(0.3, 1, len(breaks)-1))
    legend_elements = [mpatches.Patch(facecolor=colors[i], edgecolor='black', 
                                     label=labels[i]) for i in range(len(labels))]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             title='km / 10.000 hab', fontsize=10, framealpha=0.9)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "mapa_densidade_populacional_municipal.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✓ Salvo: {output_path.name}")

# =============================================================================
# MAPA 6: DENSIDADE ESPACIAL REGIONAL
# =============================================================================
def gerar_mapa_densidade_espacial_regional():
    print("\n[6/7] Gerando mapa de densidade espacial regional...")
    
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE, dpi=DPI)
    
    # Carregar dados
    regioes = gpd.read_file(DATA_DIR / "regioes_geo_indicadores.geojson")
    
    # Classificação por quantis
    valores = regioes['densidade_area_10k'].values
    breaks = criar_legenda_quantis(valores, 'Blues', n_classes=5)
    
    # Plotar
    regioes.plot(column='densidade_area_10k', ax=ax, 
                cmap='Blues', edgecolor='#000000', linewidth=1.5,
                legend=False, scheme='User_Defined',
                classification_kwds={'bins': breaks})
    
    # Adicionar nomes das regiões
    for idx, row in regioes.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(text=row['RA'], xy=(centroid.x, centroid.y),
                   ha='center', fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    configurar_mapa_base(ax, 
                        "Densidade de Malha Vicinal por Área - Escala Regional",
                        "Indicador: km de vicinais / 10.000 km² | Agregação: Regiões Administrativas")
    
    # Legenda customizada
    labels = []
    for i in range(len(breaks) - 1):
        labels.append(f"{formatar_numero(breaks[i])} - {formatar_numero(breaks[i+1])}")
    
    colors = plt.cm.Blues(np.linspace(0.3, 1, len(breaks)-1))
    legend_elements = [mpatches.Patch(facecolor=colors[i], edgecolor='black', 
                                     label=labels[i]) for i in range(len(labels))]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             title='km / 10.000 km²', fontsize=10, framealpha=0.9)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "mapa_densidade_espacial_regional.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✓ Salvo: {output_path.name}")

# =============================================================================
# MAPA 7: DENSIDADE POPULACIONAL REGIONAL
# =============================================================================
def gerar_mapa_densidade_populacional_regional():
    print("\n[7/7] Gerando mapa de densidade populacional regional...")
    
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE, dpi=DPI)
    
    # Carregar dados
    regioes = gpd.read_file(DATA_DIR / "regioes_geo_indicadores.geojson")
    
    # Classificação por quantis
    valores = regioes['densidade_pop_10k'].values
    breaks = criar_legenda_quantis(valores, 'YlOrRd', n_classes=5)
    
    # Plotar
    regioes.plot(column='densidade_pop_10k', ax=ax, 
                cmap='YlOrRd', edgecolor='#000000', linewidth=1.5,
                legend=False, scheme='User_Defined',
                classification_kwds={'bins': breaks})
    
    # Adicionar nomes das regiões
    for idx, row in regioes.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(text=row['RA'], xy=(centroid.x, centroid.y),
                   ha='center', fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    configurar_mapa_base(ax, 
                        "Densidade de Malha Vicinal por População - Escala Regional",
                        "Indicador: km de vicinais / 10.000 habitantes | Agregação: Regiões Administrativas")
    
    # Legenda customizada
    labels = []
    for i in range(len(breaks) - 1):
        labels.append(f"{formatar_numero(breaks[i])} - {formatar_numero(breaks[i+1])}")
    
    colors = plt.cm.YlOrRd(np.linspace(0.3, 1, len(breaks)-1))
    legend_elements = [mpatches.Patch(facecolor=colors[i], edgecolor='black', 
                                     label=labels[i]) for i in range(len(labels))]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             title='km / 10.000 hab', fontsize=10, framealpha=0.9)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "mapa_densidade_populacional_regional.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✓ Salvo: {output_path.name}")

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================
def main():
    print("=" * 80)
    print("GERAÇÃO DE FIGURAS - MAPAS TEMÁTICOS")
    print("Inferência Geoespacial - Malha Vicinal - Estado de São Paulo")
    print("=" * 80)
    
    # Criar diretório de saída se não existir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        gerar_mapa_malha_vicinal()
        gerar_mapa_malha_der()
        gerar_mapa_malha_completa()
        gerar_mapa_densidade_espacial_municipal()
        gerar_mapa_densidade_populacional_municipal()
        gerar_mapa_densidade_espacial_regional()
        gerar_mapa_densidade_populacional_regional()
        
        print("\n" + "=" * 80)
        print("✓ TODAS AS FIGURAS FORAM GERADAS COM SUCESSO!")
        print(f"✓ Local: {OUTPUT_DIR}")
        print("=" * 80)
        
        print("\nFIGURAS GERADAS:")
        print("  1. mapa_malha_vicinal_osm.png")
        print("  2. mapa_malha_estadual_der.png")
        print("  3. mapa_malha_completa.png")
        print("  4. mapa_densidade_espacial_municipal.png")
        print("  5. mapa_densidade_populacional_municipal.png")
        print("  6. mapa_densidade_espacial_regional.png")
        print("  7. mapa_densidade_populacional_regional.png")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
