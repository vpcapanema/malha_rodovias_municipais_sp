"""
Extração de vetores OSM do arquivo PBF para São Paulo
E criação de base com APENAS subtração da malha DER

Autor: Análise automatizada
Data: Janeiro/2026
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
from datetime import datetime
from shapely.ops import unary_union
import warnings
warnings.filterwarnings('ignore')

# Configurações
BASE_OSM = r'D:\ESTUDO_VICINAIS_V2\dados\base_linhas.gpkg'
MALHA_DER = r'D:\ESTUDO_VICINAIS_V2\dados\Sistema Rodoviário Estadual\MALHA_RODOVIARIA\MALHA_OUT.shp'
OUTPUT_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados')
RELATORIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\relatorios')

# Tolerância para buffer de subtração (em metros)
BUFFER_SUBTRACAO = 15  # metros


def log_section(titulo):
    """Imprime seção formatada"""
    print(f"\n{'='*60}")
    print(f"{titulo}")
    print(f"{'='*60}")


def carregar_dados():
    """Carrega as bases de dados"""
    log_section("CARREGANDO DADOS")
    
    print(f"Carregando base OSM: {BASE_OSM}")
    osm = gpd.read_file(BASE_OSM)
    print(f"  Total: {len(osm):,} segmentos")
    print(f"  CRS: {osm.crs}")
    
    # Estatísticas por highway
    print(f"\n  Distribuição por highway:")
    for hw, count in osm['highway'].value_counts().head(10).items():
        print(f"    {hw}: {count:,}")
    
    print(f"\nCarregando malha DER: {MALHA_DER}")
    der = gpd.read_file(MALHA_DER)
    print(f"  Total: {len(der):,} segmentos")
    print(f"  CRS: {der.crs}")
    
    # Distribuição por jurisdição
    print(f"\n  Jurisdição DER:")
    for juris, count in der['Jurisdicao'].value_counts().items():
        print(f"    {juris}: {count:,}")
    
    return osm, der


def subtrair_apenas_der(osm, der):
    """
    Subtrai APENAS a malha do DER (estadual e federal) da base OSM
    
    Não aplica nenhum outro filtro!
    - Mantém todos os tipos de highway
    - Mantém vias urbanas (residential, service, etc)
    - Mantém vias com qualquer nome
    
    Remove APENAS o que sobrepõe com rodovias estaduais/federais do DER
    """
    log_section("SUBTRAÇÃO DA MALHA DER")
    
    # Reprojetar para metros (UTM 23S)
    print("Reprojetando para sistema métrico (EPSG:31983)...")
    osm_utm = osm.to_crs(epsg=31983)
    der_utm = der.to_crs(epsg=31983)
    
    # Filtrar apenas rodovias estaduais e federais do DER
    print("\nFiltrando rodovias estaduais e federais do DER...")
    der_estadual_federal = der_utm[der_utm['Jurisdicao'].isin(['Estadual', 'Federal'])]
    print(f"  Segmentos estaduais/federais: {len(der_estadual_federal):,}")
    
    # Calcular extensão do DER
    ext_der = der_estadual_federal.geometry.length.sum() / 1000
    print(f"  Extensão DER estadual/federal: {ext_der:,.1f} km")
    
    # Criar buffer ao redor da malha DER
    print(f"\nCriando buffer de {BUFFER_SUBTRACAO}m ao redor da malha DER...")
    der_buffer = der_estadual_federal.geometry.buffer(BUFFER_SUBTRACAO)
    der_union = unary_union(der_buffer)
    print("  Buffer criado!")
    
    # Identificar segmentos OSM que interceptam o buffer do DER
    print("\nIdentificando sobreposições com DER...")
    osm_utm = osm_utm.reset_index(drop=True)
    
    # Verificar interseção
    intersecta_der = osm_utm.geometry.intersects(der_union)
    print(f"  Segmentos que intersectam DER: {intersecta_der.sum():,}")
    
    # Calcular proporção de sobreposição para cada segmento
    print("Calculando proporção de sobreposição (pode demorar)...")
    proporcao_sobreposta = []
    
    total = len(osm_utm)
    for idx, row in osm_utm.iterrows():
        if idx % 100000 == 0:
            print(f"  Processando {idx:,}/{total:,} ({100*idx/total:.1f}%)...")
        
        if intersecta_der[idx]:
            try:
                intersecao = row.geometry.intersection(der_union)
                if not intersecao.is_empty and row.geometry.length > 0:
                    prop = intersecao.length / row.geometry.length
                else:
                    prop = 0
            except:
                prop = 0
        else:
            prop = 0
        proporcao_sobreposta.append(prop)
    
    osm_utm['prop_sobreposta'] = proporcao_sobreposta
    
    # Remover segmentos com mais de 50% sobreposto ao DER
    LIMIAR_REMOCAO = 0.5
    mascara_manter = osm_utm['prop_sobreposta'] < LIMIAR_REMOCAO
    
    removidos = (~mascara_manter).sum()
    mantidos = mascara_manter.sum()
    
    print(f"\n  Segmentos com >50% sobreposição ao DER (removidos): {removidos:,}")
    print(f"  Segmentos mantidos: {mantidos:,}")
    
    # Filtrar
    osm_filtrado = osm_utm[mascara_manter].copy()
    
    # Remover coluna temporária
    osm_filtrado = osm_filtrado.drop(columns=['prop_sobreposta'])
    
    # Calcular comprimento
    osm_filtrado['comprimento_m'] = osm_filtrado.geometry.length
    
    # Reprojetar de volta para WGS84
    osm_filtrado = osm_filtrado.to_crs(epsg=4326)
    
    return osm_filtrado, removidos


def salvar_resultados(osm_filtrado, osm_original, removidos):
    """Salva os resultados"""
    log_section("SALVANDO RESULTADOS")
    
    # Nome do arquivo
    output_file = OUTPUT_DIR / 'osm_sp_menos_der.gpkg'
    print(f"Salvando: {output_file}")
    osm_filtrado.to_file(output_file, driver='GPKG')
    
    # Estatísticas
    ext_original = osm_original.to_crs(epsg=31983).geometry.length.sum() / 1000
    ext_final = osm_filtrado['comprimento_m'].sum() / 1000
    
    # Relatório
    relatorio_file = RELATORIO_DIR / 'relatorio_subtracao_der.txt'
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE SUBTRAÇÃO DA MALHA DER\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("PARÂMETROS\n")
        f.write("-"*40 + "\n")
        f.write(f"Buffer de subtração: {BUFFER_SUBTRACAO}m\n")
        f.write(f"Limiar de remoção: >50% sobreposição\n\n")
        
        f.write("RESULTADOS\n")
        f.write("-"*40 + "\n")
        f.write(f"Base OSM original: {len(osm_original):,} segmentos\n")
        f.write(f"Extensão original: {ext_original:,.1f} km\n\n")
        f.write(f"Segmentos removidos (sobrepostos ao DER): {removidos:,}\n")
        f.write(f"Segmentos finais: {len(osm_filtrado):,}\n")
        f.write(f"Extensão final: {ext_final:,.1f} km\n\n")
        
        f.write("DISTRIBUIÇÃO POR HIGHWAY (resultado)\n")
        f.write("-"*40 + "\n")
        f.write(osm_filtrado['highway'].value_counts().to_string())
    
    print(f"Relatório salvo: {relatorio_file}")
    
    return output_file, ext_original, ext_final


def main():
    print("="*60)
    print("SUBTRAÇÃO DA MALHA DER DA BASE OSM")
    print("(Sem nenhum outro filtro)")
    print("="*60)
    
    # 1. Carregar dados
    osm, der = carregar_dados()
    
    # 2. Subtrair apenas a malha DER
    osm_filtrado, removidos = subtrair_apenas_der(osm, der)
    
    # 3. Salvar resultados
    output, ext_orig, ext_final = salvar_resultados(osm_filtrado, osm, removidos)
    
    # Resumo final
    log_section("RESUMO FINAL")
    print(f"Base original: {len(osm):,} segmentos")
    print(f"Removidos (DER): {removidos:,} segmentos")
    print(f"Base final: {len(osm_filtrado):,} segmentos")
    print(f"\nExtensão original: {ext_orig:,.1f} km")
    print(f"Extensão final: {ext_final:,.1f} km")
    print(f"\nArquivo gerado: {output}")
    print("\n✅ Processamento concluído!")
    
    return osm_filtrado


if __name__ == "__main__":
    resultado = main()
