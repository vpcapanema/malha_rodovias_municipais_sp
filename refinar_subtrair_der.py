"""
Refinamento da Malha Municipal - Subtração da Malha DER e Análise de Conectividade

Este script:
1. Subtrai a malha do DER (Sistema Rodoviário Estadual) da base municipal
2. Analisa a conectividade entre a malha municipal e o SRE

Autor: Análise automatizada
Data: Janeiro/2026
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import unary_union, nearest_points
import warnings
warnings.filterwarnings('ignore')

# Configurações
INPUT_MALHA_MUNICIPAL = r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados\malha_municipal_sp.gpkg'
INPUT_MALHA_DER = r'D:\ESTUDO_VICINAIS_V2\dados\Sistema Rodoviário Estadual\MALHA_RODOVIARIA\MALHA_OUT.shp'
OUTPUT_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados')
INTERMEDIARIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\intermediarios')
RELATORIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\relatorios')

# Tolerância para buffer de subtração (em metros)
BUFFER_SUBTRACAO_M = 15  # 15 metros para capturar sobreposições

# Tolerância para conectividade (em metros)
TOLERANCIA_CONEXAO_M = 50  # 50 metros para considerar conectado


def carregar_dados():
    """Carrega as duas bases de dados"""
    print("=" * 60)
    print("CARREGANDO DADOS")
    print("=" * 60)
    
    print(f"\nCarregando malha municipal: {INPUT_MALHA_MUNICIPAL}")
    municipal = gpd.read_file(INPUT_MALHA_MUNICIPAL)
    print(f"  Registros: {len(municipal):,}")
    print(f"  CRS: {municipal.crs}")
    
    print(f"\nCarregando malha DER: {INPUT_MALHA_DER}")
    der = gpd.read_file(INPUT_MALHA_DER)
    print(f"  Registros: {len(der):,}")
    print(f"  CRS: {der.crs}")
    
    # Garantir mesmo CRS (usar SIRGAS 2000 UTM 23S para cálculos em metros)
    CRS_TRABALHO = 'EPSG:31983'  # SIRGAS 2000 UTM 23S
    
    print(f"\nReprojetando para {CRS_TRABALHO}...")
    municipal = municipal.to_crs(CRS_TRABALHO)
    der = der.to_crs(CRS_TRABALHO)
    
    return municipal, der


def subtrair_malha_der(municipal, der):
    """
    Remove segmentos da malha municipal que se sobrepõem à malha DER.
    
    Estratégia:
    1. Criar buffer ao redor da malha DER
    2. Identificar segmentos municipais que estão majoritariamente dentro do buffer
    3. Remover esses segmentos
    """
    print("\n" + "=" * 60)
    print("ETAPA 1: SUBTRAÇÃO DA MALHA DER")
    print("=" * 60)
    
    total_inicial = len(municipal)
    ext_inicial = municipal['comprimento_m'].sum() / 1000
    
    print(f"\nMalha municipal inicial: {total_inicial:,} segmentos ({ext_inicial:,.1f} km)")
    
    # Criar buffer ao redor da malha DER
    print(f"\nCriando buffer de {BUFFER_SUBTRACAO_M}m ao redor da malha DER...")
    der_buffer = der.geometry.buffer(BUFFER_SUBTRACAO_M)
    der_union = unary_union(der_buffer)
    print("  Buffer criado!")
    
    # Identificar segmentos municipais que intersectam o buffer do DER
    print("\nIdentificando sobreposições...")
    
    # Calcular quanto de cada segmento está dentro do buffer
    def calcular_sobreposicao(geom):
        """Calcula a porcentagem do segmento dentro do buffer DER"""
        try:
            if geom is None or geom.is_empty:
                return 0.0
            intersecao = geom.intersection(der_union)
            if intersecao.is_empty:
                return 0.0
            return intersecao.length / geom.length * 100
        except:
            return 0.0
    
    municipal['pct_sobreposicao_der'] = municipal.geometry.apply(calcular_sobreposicao)
    
    # Estatísticas de sobreposição
    print(f"\nDistribuição de sobreposição com DER:")
    print(f"  0%: {(municipal['pct_sobreposicao_der'] == 0).sum():,} segmentos")
    print(f"  1-50%: {((municipal['pct_sobreposicao_der'] > 0) & (municipal['pct_sobreposicao_der'] <= 50)).sum():,} segmentos")
    print(f"  51-99%: {((municipal['pct_sobreposicao_der'] > 50) & (municipal['pct_sobreposicao_der'] < 100)).sum():,} segmentos")
    print(f"  100%: {(municipal['pct_sobreposicao_der'] == 100).sum():,} segmentos")
    
    # Remover segmentos com mais de 70% de sobreposição
    LIMIAR_REMOCAO = 70  # Remover se mais de 70% está sobreposto ao DER
    
    mask_manter = municipal['pct_sobreposicao_der'] < LIMIAR_REMOCAO
    municipal_filtrado = municipal[mask_manter].copy()
    
    removidos = total_inicial - len(municipal_filtrado)
    ext_final = municipal_filtrado['comprimento_m'].sum() / 1000
    
    print(f"\n{'='*40}")
    print(f"RESULTADO DA SUBTRAÇÃO (limiar: {LIMIAR_REMOCAO}%)")
    print(f"{'='*40}")
    print(f"Segmentos removidos: {removidos:,}")
    print(f"Segmentos restantes: {len(municipal_filtrado):,}")
    print(f"Extensão final: {ext_final:,.1f} km")
    print(f"Extensão removida: {ext_inicial - ext_final:,.1f} km")
    
    # Remover coluna temporária
    municipal_filtrado = municipal_filtrado.drop(columns=['pct_sobreposicao_der'])
    
    return municipal_filtrado, removidos


def analisar_conectividade(municipal, der):
    """
    Analisa a conectividade entre a malha municipal e o SRE (DER).
    
    Verifica:
    1. Quantos segmentos municipais tocam a malha DER
    2. Identifica pontos de conexão
    3. Identifica segmentos "órfãos" (não conectados)
    """
    print("\n" + "=" * 60)
    print("ETAPA 2: ANÁLISE DE CONECTIVIDADE COM SRE")
    print("=" * 60)
    
    # Criar buffer de conexão ao redor do DER
    print(f"\nCriando buffer de conexão ({TOLERANCIA_CONEXAO_M}m) ao redor do SRE...")
    der_buffer_conexao = der.geometry.buffer(TOLERANCIA_CONEXAO_M)
    der_union_conexao = unary_union(der_buffer_conexao)
    
    # Extrair pontos extremos (início e fim) de cada segmento municipal
    print("Extraindo pontos extremos dos segmentos municipais...")
    
    def get_endpoints(geom):
        """Retorna os pontos de início e fim de uma linha"""
        if isinstance(geom, LineString):
            return [Point(geom.coords[0]), Point(geom.coords[-1])]
        elif isinstance(geom, MultiLineString):
            points = []
            for line in geom.geoms:
                points.append(Point(line.coords[0]))
                points.append(Point(line.coords[-1]))
            return points
        return []
    
    # Verificar conexão de cada segmento
    def verifica_conexao_sre(geom):
        """Verifica se algum ponto extremo toca o buffer do SRE"""
        endpoints = get_endpoints(geom)
        for pt in endpoints:
            if pt.within(der_union_conexao):
                return True
        return False
    
    print("Verificando conexões...")
    municipal['conectado_sre'] = municipal.geometry.apply(verifica_conexao_sre)
    
    # Estatísticas de conectividade
    conectados = municipal['conectado_sre'].sum()
    nao_conectados = len(municipal) - conectados
    
    print(f"\n{'='*40}")
    print("RESULTADO DA ANÁLISE DE CONECTIVIDADE")
    print(f"{'='*40}")
    print(f"Segmentos conectados ao SRE: {conectados:,} ({100*conectados/len(municipal):.1f}%)")
    print(f"Segmentos não conectados: {nao_conectados:,} ({100*nao_conectados/len(municipal):.1f}%)")
    
    # Criar coluna de classificação
    municipal['status_conexao'] = municipal['conectado_sre'].map({
        True: 'conectado_sre',
        False: 'nao_conectado'
    })
    
    # Análise por tipo de highway
    print(f"\nConectividade por tipo de highway:")
    for hw in municipal['highway'].unique():
        subset = municipal[municipal['highway'] == hw]
        pct_conectado = 100 * subset['conectado_sre'].sum() / len(subset)
        print(f"  {hw}: {pct_conectado:.1f}% conectado ({subset['conectado_sre'].sum():,}/{len(subset):,})")
    
    return municipal


def identificar_pontos_conexao(municipal, der):
    """
    Identifica os pontos de conexão entre a malha municipal e o SRE.
    Gera um arquivo de pontos para visualização.
    """
    print("\n" + "=" * 60)
    print("ETAPA 3: IDENTIFICAÇÃO DE PONTOS DE CONEXÃO")
    print("=" * 60)
    
    # Usar apenas segmentos conectados
    conectados = municipal[municipal['conectado_sre'] == True].copy()
    
    print(f"Analisando {len(conectados):,} segmentos conectados...")
    
    # Buffer do DER
    der_buffer = der.geometry.buffer(TOLERANCIA_CONEXAO_M)
    der_union = unary_union(der_buffer)
    
    # Extrair pontos de conexão
    pontos_conexao = []
    
    def get_endpoints(geom):
        if isinstance(geom, LineString):
            return [Point(geom.coords[0]), Point(geom.coords[-1])]
        elif isinstance(geom, MultiLineString):
            points = []
            for line in geom.geoms:
                points.append(Point(line.coords[0]))
                points.append(Point(line.coords[-1]))
            return points
        return []
    
    for idx, row in conectados.iterrows():
        endpoints = get_endpoints(row.geometry)
        for pt in endpoints:
            if pt.within(der_union):
                pontos_conexao.append({
                    'geometry': pt,
                    'highway_origem': row['highway'],
                    'nome_origem': row.get('name', '')
                })
    
    # Criar GeoDataFrame de pontos
    if pontos_conexao:
        gdf_pontos = gpd.GeoDataFrame(pontos_conexao, crs=municipal.crs)
        
        # Remover pontos duplicados (muito próximos)
        print(f"Pontos de conexão brutos: {len(gdf_pontos):,}")
        
        # Agrupar pontos muito próximos (buffer de 10m)
        gdf_pontos['cluster'] = -1
        cluster_id = 0
        
        for i, row in gdf_pontos.iterrows():
            if gdf_pontos.loc[i, 'cluster'] == -1:
                # Encontrar pontos próximos
                buffer_pt = row.geometry.buffer(10)
                proximos = gdf_pontos[gdf_pontos.geometry.within(buffer_pt)].index
                gdf_pontos.loc[proximos, 'cluster'] = cluster_id
                cluster_id += 1
        
        # Pegar um ponto por cluster
        gdf_pontos_unicos = gdf_pontos.groupby('cluster').first().reset_index()
        gdf_pontos_unicos = gpd.GeoDataFrame(gdf_pontos_unicos, crs=municipal.crs)
        
        print(f"Pontos de conexão únicos: {len(gdf_pontos_unicos):,}")
        
        return gdf_pontos_unicos
    
    return gpd.GeoDataFrame(columns=['geometry'], crs=municipal.crs)


def salvar_resultados(municipal, pontos_conexao, der, removidos):
    """Salva os resultados e gera relatórios"""
    print("\n" + "=" * 60)
    print("SALVANDO RESULTADOS")
    print("=" * 60)
    
    # Converter de volta para WGS84 para salvar
    CRS_SAIDA = 'EPSG:4326'
    municipal_saida = municipal.to_crs(CRS_SAIDA)
    pontos_saida = pontos_conexao.to_crs(CRS_SAIDA) if len(pontos_conexao) > 0 else pontos_conexao
    
    # 1. Malha municipal refinada (sem sobreposição com DER)
    arquivo_municipal = OUTPUT_DIR / 'malha_municipal_sp_refinada.gpkg'
    print(f"\nSalvando malha refinada: {arquivo_municipal}")
    # Remover colunas de análise para o arquivo final
    colunas_saida = ['name', 'highway', 'ref', 'other_tags', 'comprimento_m', 'status_conexao', 'geometry']
    municipal_saida[[c for c in colunas_saida if c in municipal_saida.columns]].to_file(
        arquivo_municipal, driver='GPKG'
    )
    
    # 2. Segmentos conectados ao SRE
    arquivo_conectados = INTERMEDIARIO_DIR / 'segmentos_conectados_sre.gpkg'
    print(f"Salvando segmentos conectados: {arquivo_conectados}")
    municipal_saida[municipal_saida['status_conexao'] == 'conectado_sre'].to_file(
        arquivo_conectados, driver='GPKG'
    )
    
    # 3. Segmentos NÃO conectados (para análise)
    arquivo_nao_conectados = INTERMEDIARIO_DIR / 'segmentos_nao_conectados.gpkg'
    print(f"Salvando segmentos não conectados: {arquivo_nao_conectados}")
    municipal_saida[municipal_saida['status_conexao'] == 'nao_conectado'].to_file(
        arquivo_nao_conectados, driver='GPKG'
    )
    
    # 4. Pontos de conexão
    if len(pontos_saida) > 0:
        arquivo_pontos = OUTPUT_DIR / 'pontos_conexao_sre.gpkg'
        print(f"Salvando pontos de conexão: {arquivo_pontos}")
        pontos_saida.to_file(arquivo_pontos, driver='GPKG')
    
    # 5. Relatório
    relatorio_file = RELATORIO_DIR / 'relatorio_refinamento_der.txt'
    print(f"\nGerando relatório: {relatorio_file}")
    
    conectados = (municipal['status_conexao'] == 'conectado_sre').sum()
    nao_conectados = (municipal['status_conexao'] == 'nao_conectado').sum()
    
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE REFINAMENTO - SUBTRAÇÃO DER E CONECTIVIDADE\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("1. SUBTRAÇÃO DA MALHA DER\n")
        f.write("-" * 40 + "\n")
        f.write(f"Buffer de subtração: {BUFFER_SUBTRACAO_M}m\n")
        f.write(f"Segmentos removidos: {removidos:,}\n\n")
        
        f.write("2. ANÁLISE DE CONECTIVIDADE\n")
        f.write("-" * 40 + "\n")
        f.write(f"Tolerância de conexão: {TOLERANCIA_CONEXAO_M}m\n")
        f.write(f"Segmentos conectados ao SRE: {conectados:,} ({100*conectados/len(municipal):.1f}%)\n")
        f.write(f"Segmentos não conectados: {nao_conectados:,} ({100*nao_conectados/len(municipal):.1f}%)\n")
        f.write(f"Pontos de conexão identificados: {len(pontos_conexao):,}\n\n")
        
        f.write("3. RESULTADO FINAL\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total de segmentos: {len(municipal):,}\n")
        f.write(f"Extensão total: {municipal['comprimento_m'].sum()/1000:,.1f} km\n\n")
        
        f.write("4. DISTRIBUIÇÃO POR HIGHWAY\n")
        f.write("-" * 40 + "\n")
        f.write(municipal['highway'].value_counts().to_string())
        f.write("\n\n")
        
        f.write("5. CONECTIVIDADE POR HIGHWAY\n")
        f.write("-" * 40 + "\n")
        for hw in municipal['highway'].unique():
            subset = municipal[municipal['highway'] == hw]
            pct = 100 * subset['conectado_sre'].sum() / len(subset)
            f.write(f"{hw}: {pct:.1f}% conectado\n")
    
    print("\n✅ Resultados salvos!")


def main():
    print("=" * 60)
    print("REFINAMENTO DA MALHA MUNICIPAL")
    print("Subtração DER + Análise de Conectividade")
    print("=" * 60)
    
    # Carregar dados
    municipal, der = carregar_dados()
    
    # Etapa 1: Subtrair malha DER
    municipal_refinado, removidos = subtrair_malha_der(municipal, der)
    
    # Etapa 2: Analisar conectividade
    municipal_conectividade = analisar_conectividade(municipal_refinado, der)
    
    # Etapa 3: Identificar pontos de conexão
    pontos_conexao = identificar_pontos_conexao(municipal_conectividade, der)
    
    # Salvar resultados
    salvar_resultados(municipal_conectividade, pontos_conexao, der, removidos)
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    conectados = (municipal_conectividade['status_conexao'] == 'conectado_sre').sum()
    print(f"Segmentos na malha municipal refinada: {len(municipal_conectividade):,}")
    print(f"Extensão total: {municipal_conectividade['comprimento_m'].sum()/1000:,.1f} km")
    print(f"Conectados ao SRE: {conectados:,} ({100*conectados/len(municipal_conectividade):.1f}%)")
    print(f"Pontos de conexão: {len(pontos_conexao):,}")
    
    return municipal_conectividade, pontos_conexao


if __name__ == "__main__":
    resultado, pontos = main()
