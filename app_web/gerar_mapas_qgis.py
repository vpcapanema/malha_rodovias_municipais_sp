"""
Script para gerar os 4 mapas temáticos da análise de vicinais
Requisitos: PyQGIS instalado (QGIS 3.x)
Uso: Executar dentro do Console Python do QGIS ou via qgis_process
"""

import os
from pathlib import Path

# Configurações
GPKG_PATH = r"D:\ESTUDO_VICINAIS_V2\resultados\dados_processados\malha_municipal_sp.gpkg"
OUTPUT_DIR = r"D:\ESTUDO_VICINAIS_V2\app_web\images"
WIDTH = 1920
HEIGHT = 1080

# Criar diretório de saída se não existir
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def criar_mapa_1_densidade_territorial():
    """
    Mapa 1: Densidade Territorial (km/10.000km²)
    Paleta: Reds - 5 classes (Quebras Naturais)
    """
    print("Gerando Mapa 1: Densidade Territorial...")
    
    # TODO: Implementar com PyQGIS
    # 1. Carregar malha_municipal_sp.gpkg
    # 2. Aplicar simbologia graduada em 'densidade_km_10000km2'
    # 3. Método: Jenks (Natural Breaks) - 5 classes
    # 4. Paleta de cores: Reds (vermelho crescente)
    # 5. Exportar para images/mapa1_densidade_territorial.png
    
    print("  → Instruções manuais:")
    print("     - Abrir QGIS e carregar malha_municipal_sp.gpkg")
    print("     - Simbologia → Graduado → Campo: densidade_km_10000km2")
    print("     - Modo: Quebras Naturais (Jenks) → 5 classes")
    print("     - Rampa de cor: Reds")
    print(f"     - Exportar layout como PNG {WIDTH}x{HEIGHT}px")
    print(f"     - Salvar em: {OUTPUT_DIR}/mapa1_densidade_territorial.png")

def criar_mapa_2_densidade_per_capita():
    """
    Mapa 2: Densidade per Capita (km/10.000 hab)
    Paleta: Oranges - 5 classes (Quantis)
    """
    print("\nGerando Mapa 2: Densidade per Capita...")
    
    print("  → Instruções manuais:")
    print("     - Campo: densidade_km_10000hab")
    print("     - Modo: Quantis → 5 classes (distribuição equilibrada)")
    print("     - Rampa de cor: Oranges")
    print("     - Adicionar rótulos para municípios com > 20 km/10.000 hab")
    print(f"     - Salvar em: {OUTPUT_DIR}/mapa2_densidade_per_capita.png")

def criar_mapa_3_razao_osm_der():
    """
    Mapa 3: Razão OSM/DER
    Paleta: RdYlGn invertida - Classes manuais
    """
    print("\nGerando Mapa 3: Razão OSM/DER...")
    
    print("  → Instruções manuais:")
    print("     - Campo: razao_osm_der")
    print("     - Modo: Quebras Manuais → Classes: <2, 2-5, 5-10, 10-15, >15")
    print("     - Rampa de cor: RdYlGn (vermelho = alta divergência)")
    print("     - Adicionar camada DER como linhas cinzas para referência")
    print(f"     - Salvar em: {OUTPUT_DIR}/mapa3_razao_osm_der.png")

def criar_mapa_4_regioes_administrativas():
    """
    Mapa 4: Agregação por Região Administrativa
    Paleta: Spectral - 16 classes (uma por RA)
    """
    print("\nGerando Mapa 4: Regiões Administrativas...")
    
    print("  → Instruções manuais:")
    print("     - Dissolver municípios por 'regiao_administrativa'")
    print("     - Calcular densidade agregada para cada RA")
    print("     - Simbologia: Diagrama de barras ou círculos proporcionais")
    print("     - Paleta: Spectral (16 cores distintas)")
    print("     - Rótulos com nome da RA e densidade total")
    print(f"     - Salvar em: {OUTPUT_DIR}/mapa4_regioes_administrativas.png")

if __name__ == "__main__":
    print("=" * 60)
    print("GERADOR DE MAPAS TEMÁTICOS - VICINAIS SP")
    print("=" * 60)
    print(f"\nArquivo de entrada: {GPKG_PATH}")
    print(f"Diretório de saída: {OUTPUT_DIR}")
    print(f"Resolução: {WIDTH}x{HEIGHT}px\n")
    
    if not os.path.exists(GPKG_PATH):
        print(f"ERRO: Arquivo não encontrado: {GPKG_PATH}")
        print("Execute o processamento de dados antes de gerar os mapas.")
        exit(1)
    
    print("\n" + "-" * 60)
    criar_mapa_1_densidade_territorial()
    print("-" * 60)
    criar_mapa_2_densidade_per_capita()
    print("-" * 60)
    criar_mapa_3_razao_osm_der()
    print("-" * 60)
    criar_mapa_4_regioes_administrativas()
    print("-" * 60)
    
    print("\n✓ Instruções exibidas com sucesso!")
    print("\nNOTA: Este script fornece instruções manuais.")
    print("Para automação completa, implemente as funções com PyQGIS.")
    print("\nReferência PyQGIS: https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/")
