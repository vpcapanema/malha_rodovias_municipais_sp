"""
Extração da Malha Viária Municipal do Estado de São Paulo
Metodologia: Exclusão progressiva de vias federais, estaduais e urbanas

Autor: Análise automatizada
Data: Janeiro/2026
"""

import geopandas as gpd
import pandas as pd
import re
from pathlib import Path

# Configurações
INPUT_FILE = r'D:\ESTUDO_VICINAIS_V2\dados\base_linhas.gpkg'
OUTPUT_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados')
INTERMEDIARIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\intermediarios')
RELATORIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\relatorios')
AU_IBGE_FILE = r'D:\ESTUDO_VICINAIS_V2\dados\au_ibge.gpkg'

def log_stats(gdf, etapa, descricao):
    """Loga estatísticas de cada etapa"""
    print(f"\n{'='*60}")
    print(f"ETAPA {etapa}: {descricao}")
    print(f"{'='*60}")
    print(f"Total de registros: {len(gdf):,}")
    if 'highway' in gdf.columns:
        print(f"\nDistribuição por highway:")
        print(gdf['highway'].value_counts().head(10).to_string())
    return len(gdf)

def etapa1_filtro_highway(gdf):
    """
    ETAPA 1: Excluir tipos de highway que são claramente não-municipais ou urbanas
    
    Excluir:
    - motorway, motorway_link: Autoestradas (sempre estaduais/federais)
    - trunk, trunk_link: Rodovias principais (estaduais/federais)
    - residential: Ruas residenciais (urbanas - prefeitura)
    - living_street: Zonas de tráfego calmo (urbanas)
    - service: Vias de serviço (urbanas/privadas)
    """
    
    excluir_highway = [
        'motorway', 'motorway_link',
        'trunk', 'trunk_link',
        'residential', 'living_street',
        'service'
    ]
    
    # Filtrar
    mask = ~gdf['highway'].isin(excluir_highway)
    resultado = gdf[mask].copy()
    
    print(f"\nTipos excluídos: {excluir_highway}")
    print(f"Registros removidos: {len(gdf) - len(resultado):,}")
    
    return resultado

def etapa2_filtro_referencia(gdf):
    """
    ETAPA 2: Excluir vias com referência de rodovia federal (BR-) ou estadual (SP-)
    
    IMPORTANTE: Manter códigos municipais:
    - SPA-xxx (Estrada Vicinal Acesso)
    - SPI-xxx (Estrada Vicinal Interna)
    - SPM-xxx (Estrada Municipal)
    """
    
    def is_federal_ou_estadual(ref):
        """Verifica se a referência é de rodovia federal ou estadual"""
        if pd.isna(ref):
            return False
        
        ref_upper = str(ref).upper()
        
        # Padrão de rodovia federal: BR-xxx
        if re.search(r'\bBR-\d+', ref_upper):
            return True
        
        # Padrão de rodovia estadual: SP-xxx (mas não SPA, SPI, SPM que são municipais)
        # SP-xxx onde xxx são números
        if re.search(r'\bSP-\d+', ref_upper):
            # Verificar se NÃO é código municipal
            if not re.search(r'\bSP[AIM]-', ref_upper):
                return True
        
        return False
    
    # Aplicar filtro
    mask_federal_estadual = gdf['ref'].apply(is_federal_ou_estadual)
    resultado = gdf[~mask_federal_estadual].copy()
    
    print(f"\nRegistros com ref BR/SP removidos: {mask_federal_estadual.sum():,}")
    
    # Mostrar exemplos de refs mantidas
    refs_mantidas = resultado[resultado['ref'].notna()]['ref'].value_counts().head(10)
    print(f"\nTop 10 refs MANTIDAS (municipais):")
    print(refs_mantidas.to_string())
    
    return resultado

def etapa3_filtro_nomes_urbanos(gdf):
    """
    ETAPA 3: Excluir vias com nomes tipicamente urbanos
    
    Excluir:
    - Rua, Avenida, Travessa, Alameda, Praça, Viela, Largo, Beco, Passagem
    
    Manter:
    - Estrada, Rodovia, Vicinal, Acesso, Caminho
    """
    
    padroes_urbanos = [
        r'^Rua\s',
        r'^Avenida\s',
        r'^Av\.\s',
        r'^Travessa\s',
        r'^Alameda\s',
        r'^Praça\s',
        r'^Viela\s',
        r'^Largo\s',
        r'^Beco\s',
        r'^Passagem\s',
        r'^Ladeira\s',
        r'^Passeio\s',
    ]
    
    def is_nome_urbano(nome):
        """Verifica se o nome indica via urbana"""
        if pd.isna(nome):
            return False
        
        nome_str = str(nome)
        for padrao in padroes_urbanos:
            if re.search(padrao, nome_str, re.IGNORECASE):
                return True
        return False
    
    # Aplicar filtro
    mask_urbano = gdf['name'].apply(is_nome_urbano)
    resultado = gdf[~mask_urbano].copy()
    
    print(f"\nRegistros com nomes urbanos removidos: {mask_urbano.sum():,}")
    
    # Mostrar exemplos de nomes mantidos
    nomes_mantidos = resultado[resultado['name'].notna()]['name'].value_counts().head(15)
    print(f"\nTop 15 nomes MANTIDOS:")
    print(nomes_mantidos.to_string())
    
    return resultado

def etapa4_filtro_espacial_au(gdf, au_file):
    """
    ETAPA 4 (OPCIONAL): Excluir vias dentro de áreas urbanas IBGE
    
    Usa o arquivo au_ibge.gpkg para remover vias que estão
    completamente dentro de áreas urbanas.
    """
    
    print("\nCarregando áreas urbanas IBGE...")
    au = gpd.read_file(au_file)
    
    # Garantir mesmo CRS
    if gdf.crs != au.crs:
        au = au.to_crs(gdf.crs)
    
    print(f"Total de polígonos AU: {len(au):,}")
    
    # Dissolver todas as áreas urbanas em um único polígono (mais eficiente)
    print("Dissolvendo áreas urbanas...")
    au_dissolved = au.dissolve()
    
    # Verificar quais vias estão DENTRO de áreas urbanas
    print("Identificando vias dentro de AU...")
    
    # Usar sjoin para eficiência
    vias_em_au = gpd.sjoin(gdf, au_dissolved, predicate='within', how='inner')
    indices_em_au = set(vias_em_au.index)
    
    # Filtrar vias que NÃO estão em AU
    resultado = gdf[~gdf.index.isin(indices_em_au)].copy()
    
    print(f"\nVias dentro de AU removidas: {len(indices_em_au):,}")
    
    return resultado

def calcular_comprimento(gdf):
    """Calcula comprimento em metros (reprojetando para UTM)"""
    # Usar UTM zona 23S (EPSG:31983) para SP
    gdf_utm = gdf.to_crs(epsg=31983)
    gdf['comprimento_m'] = gdf_utm.geometry.length
    return gdf

def main():
    print("="*60)
    print("EXTRAÇÃO DA MALHA VIÁRIA MUNICIPAL - ESTADO DE SÃO PAULO")
    print("="*60)
    
    # Carregar dados
    print(f"\nCarregando base de dados: {INPUT_FILE}")
    gdf = gpd.read_file(INPUT_FILE)
    total_inicial = log_stats(gdf, 0, "Base Original")
    
    # ETAPA 1: Filtro por Highway
    gdf_e1 = etapa1_filtro_highway(gdf)
    total_e1 = log_stats(gdf_e1, 1, "Após Filtro Highway")
    
    # ETAPA 2: Filtro por Referência
    gdf_e2 = etapa2_filtro_referencia(gdf_e1)
    total_e2 = log_stats(gdf_e2, 2, "Após Filtro Referência BR/SP")
    
    # ETAPA 3: Filtro por Nomes Urbanos
    gdf_e3 = etapa3_filtro_nomes_urbanos(gdf_e2)
    total_e3 = log_stats(gdf_e3, 3, "Após Filtro Nomes Urbanos")
    
    # Calcular comprimentos
    print("\n" + "="*60)
    print("Calculando comprimentos...")
    gdf_final = calcular_comprimento(gdf_e3)
    
    # Estatísticas finais
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    print(f"\n{'Etapa':<40} {'Registros':>15} {'% do Total':>12}")
    print("-"*67)
    print(f"{'Base Original':<40} {total_inicial:>15,} {100:>11.1f}%")
    print(f"{'Após Filtro Highway':<40} {total_e1:>15,} {100*total_e1/total_inicial:>11.1f}%")
    print(f"{'Após Filtro Referência':<40} {total_e2:>15,} {100*total_e2/total_inicial:>11.1f}%")
    print(f"{'Após Filtro Nomes Urbanos (FINAL)':<40} {total_e3:>15,} {100*total_e3/total_inicial:>11.1f}%")
    
    # Comprimento total
    comp_total_km = gdf_final['comprimento_m'].sum() / 1000
    print(f"\nComprimento total estimado: {comp_total_km:,.1f} km")
    
    # Salvar resultado intermediário (sem filtro AU)
    intermediario_file = INTERMEDIARIO_DIR / 'malha_municipal_sp_sem_filtro_au.gpkg'
    print(f"\nSalvando intermediário em: {intermediario_file}")
    
    # Selecionar colunas relevantes
    colunas_saida = ['name', 'highway', 'ref', 'other_tags', 'comprimento_m', 'geometry']
    gdf_saida = gdf_final[[c for c in colunas_saida if c in gdf_final.columns]]
    gdf_saida.to_file(intermediario_file, driver='GPKG')
    
    # Gerar relatório
    relatorio_file = RELATORIO_DIR / 'relatorio_extracao.txt'
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE EXTRAÇÃO DA MALHA VIÁRIA MUNICIPAL\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Base Original: {total_inicial:,} registros\n")
        f.write(f"Após Filtro Highway: {total_e1:,} registros\n")
        f.write(f"Após Filtro Referência: {total_e2:,} registros\n")
        f.write(f"Após Filtro Nomes Urbanos: {total_e3:,} registros\n")
        f.write(f"\nExtensão total: {comp_total_km:,.1f} km\n")
        f.write(f"\nDistribuição por highway:\n")
        f.write(gdf_final['highway'].value_counts().to_string())
    print(f"Relatório salvo em: {relatorio_file}")
    
    print("\n✅ Processamento concluído!")
    print(f"   Arquivo intermediário: {intermediario_file}")
    print(f"   Relatório: {relatorio_file}")
    print(f"   Total de segmentos: {len(gdf_final):,}")
    print(f"   Extensão total: {comp_total_km:,.1f} km")
    
    return gdf_final

if __name__ == "__main__":
    resultado = main()
