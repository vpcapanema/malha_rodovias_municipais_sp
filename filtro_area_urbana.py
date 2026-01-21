"""
Versão com Filtro Espacial por Área Urbana IBGE
Remove vias que estão DENTRO de áreas urbanas do IBGE

Este é um refinamento adicional que pode ser aplicado
após o processamento principal.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configurações
INPUT_FILE = r'D:\ESTUDO_VICINAIS_V2\resultados\intermediarios\malha_municipal_sp_sem_filtro_au.gpkg'
AU_IBGE_FILE = r'D:\ESTUDO_VICINAIS_V2\dados\au_ibge.gpkg'
OUTPUT_FILE = r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados\malha_municipal_sp.gpkg'
RELATORIO_DIR = r'D:\ESTUDO_VICINAIS_V2\resultados\relatorios'

def main():
    print("="*60)
    print("FILTRO ESPACIAL POR ÁREA URBANA IBGE")
    print("="*60)
    
    # Carregar malha municipal já processada
    print(f"\nCarregando malha municipal: {INPUT_FILE}")
    gdf = gpd.read_file(INPUT_FILE)
    print(f"Total de registros: {len(gdf):,}")
    print(f"Extensão: {gdf['comprimento_m'].sum()/1000:,.1f} km")
    
    # Carregar áreas urbanas
    print(f"\nCarregando áreas urbanas IBGE: {AU_IBGE_FILE}")
    au = gpd.read_file(AU_IBGE_FILE)
    print(f"Total de polígonos AU: {len(au):,}")
    
    # Garantir mesmo CRS
    print(f"\nCRS malha: {gdf.crs}")
    print(f"CRS AU: {au.crs}")
    
    if gdf.crs != au.crs:
        print("Reprojetando AU para o mesmo CRS...")
        au = au.to_crs(gdf.crs)
    
    # Dissolver áreas urbanas - filtrar apenas SP
    print("\nFiltrando AU apenas para SP (bounds da malha)...")
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    
    # Filtrar AU que intersectam a área de SP
    au_sp = au.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
    print(f"AU dentro dos bounds de SP: {len(au_sp):,}")
    
    # Dissolver
    print("Dissolvendo áreas urbanas (pode demorar)...")
    au_dissolved = au_sp.dissolve()
    print("Dissolução concluída!")
    
    # Identificar vias DENTRO de áreas urbanas
    print("\nIdentificando vias dentro de AU (sjoin)...")
    
    # Reset index para garantir unicidade
    gdf = gdf.reset_index(drop=True)
    
    # Spatial join - vias que estão DENTRO de AU
    vias_em_au = gpd.sjoin(gdf, au_dissolved, predicate='within', how='inner')
    indices_em_au = set(vias_em_au.index)
    
    print(f"Vias completamente dentro de AU: {len(indices_em_au):,}")
    
    # Filtrar vias FORA de AU
    gdf_fora_au = gdf[~gdf.index.isin(indices_em_au)].copy()
    
    print(f"\n{'='*60}")
    print("RESULTADO DO FILTRO ESPACIAL")
    print(f"{'='*60}")
    print(f"Vias antes do filtro AU: {len(gdf):,}")
    print(f"Vias removidas (dentro AU): {len(indices_em_au):,}")
    print(f"Vias restantes (fora AU): {len(gdf_fora_au):,}")
    print(f"Extensão final: {gdf_fora_au['comprimento_m'].sum()/1000:,.1f} km")
    
    # Distribuição por highway
    print(f"\nDistribuição por highway:")
    print(gdf_fora_au['highway'].value_counts().to_string())
    
    # Salvar resultado final
    print(f"\nSalvando resultado em: {OUTPUT_FILE}")
    gdf_fora_au.to_file(OUTPUT_FILE, driver='GPKG')
    
    # Gerar relatório do filtro AU
    relatorio_file = Path(RELATORIO_DIR) / 'relatorio_filtro_au.txt'
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE FILTRO POR ÁREA URBANA IBGE\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Vias antes do filtro AU: {len(gdf):,}\n")
        f.write(f"Polígonos AU (SP): {len(au_sp):,}\n")
        f.write(f"Vias removidas (dentro AU): {len(indices_em_au):,}\n")
        f.write(f"Vias restantes (fora AU): {len(gdf_fora_au):,}\n")
        f.write(f"\nExtensão final: {gdf_fora_au['comprimento_m'].sum()/1000:,.1f} km\n")
        f.write(f"\nDistribuição por highway:\n")
        f.write(gdf_fora_au['highway'].value_counts().to_string())
    print(f"Relatório salvo em: {relatorio_file}")
    
    print("\n✅ Processamento concluído!")
    print(f"   Arquivo final: {OUTPUT_FILE}")
    
    return gdf_fora_au

if __name__ == "__main__":
    resultado = main()
