"""
Refinamento da Malha Municipal - Subtração do SRE e Análise de Conectividade

Este script:
1. Subtrai a malha do DER (Sistema Rodoviário Estadual) da malha municipal
2. Analisa a conectividade entre a malha municipal e o SRE
3. Identifica segmentos desconectados

Autor: Análise automatizada
Data: Janeiro/2026
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from shapely.ops import unary_union
from shapely.geometry import Point, LineString, MultiLineString
import warnings
warnings.filterwarnings('ignore')

# Configurações
MALHA_MUNICIPAL = r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados\malha_municipal_sp.gpkg'
MALHA_DER = r'D:\ESTUDO_VICINAIS_V2\dados\Sistema Rodoviário Estadual\MALHA_RODOVIARIA\MALHA_OUT.shp'
OUTPUT_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados')
INTERMEDIARIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\intermediarios')
RELATORIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\relatorios')

# Tolerância para buffer de subtração (em metros)
BUFFER_SUBTRACAO = 15  # metros
# Tolerância para conectividade (em metros)
TOLERANCIA_CONEXAO = 50  # metros


def log_section(titulo):
    """Imprime seção formatada"""
    print(f"\n{'='*60}")
    print(f"{titulo}")
    print(f"{'='*60}")


def carregar_dados():
    """Carrega as bases de dados"""
    log_section("CARREGANDO DADOS")
    
    print(f"Carregando malha municipal: {MALHA_MUNICIPAL}")
    municipal = gpd.read_file(MALHA_MUNICIPAL)
    print(f"  Total: {len(municipal):,} segmentos")
    print(f"  CRS: {municipal.crs}")
    
    print(f"\nCarregando malha DER: {MALHA_DER}")
    der = gpd.read_file(MALHA_DER)
    print(f"  Total: {len(der):,} segmentos")
    print(f"  CRS: {der.crs}")
    
    # Distribuição por jurisdição
    print(f"\n  Jurisdição DER:")
    for juris, count in der['Jurisdicao'].value_counts().items():
        print(f"    {juris}: {count:,}")
    
    return municipal, der


def reprojetar_para_metros(gdf, crs_metros=31983):
    """Reprojeta para sistema de coordenadas em metros (UTM 23S)"""
    if gdf.crs.to_epsg() != crs_metros:
        return gdf.to_crs(epsg=crs_metros)
    return gdf


def subtrair_malha_der(municipal, der):
    """
    Subtrai a malha do DER da malha municipal usando buffer espacial
    
    Remove segmentos que sobrepõem com a malha estadual/federal
    """
    log_section("ETAPA 1: SUBTRAÇÃO DA MALHA DER")
    
    # Reprojetar para metros
    print("Reprojetando para sistema métrico (EPSG:31983)...")
    municipal_utm = reprojetar_para_metros(municipal)
    der_utm = reprojetar_para_metros(der)
    
    # Filtrar apenas rodovias estaduais e federais do DER
    print("\nFiltrando rodovias estaduais e federais do DER...")
    der_estadual_federal = der_utm[der_utm['Jurisdicao'].isin(['Estadual', 'Federal'])]
    print(f"  Segmentos estaduais/federais: {len(der_estadual_federal):,}")
    
    # Criar buffer ao redor da malha DER
    print(f"\nCriando buffer de {BUFFER_SUBTRACAO}m ao redor da malha DER...")
    der_buffer = der_estadual_federal.geometry.buffer(BUFFER_SUBTRACAO)
    der_union = unary_union(der_buffer)
    print("  Buffer criado!")
    
    # Identificar segmentos municipais que interceptam o buffer do DER
    print("\nIdentificando sobreposições...")
    municipal_utm = municipal_utm.reset_index(drop=True)
    
    # Verificar interseção
    intersecta_der = municipal_utm.geometry.intersects(der_union)
    
    # Calcular proporção de sobreposição para cada segmento
    print("Calculando proporção de sobreposição...")
    proporcao_sobreposta = []
    
    for idx, row in municipal_utm.iterrows():
        if intersecta_der[idx]:
            try:
                intersecao = row.geometry.intersection(der_union)
                if not intersecao.is_empty:
                    prop = intersecao.length / row.geometry.length
                else:
                    prop = 0
            except:
                prop = 0
        else:
            prop = 0
        proporcao_sobreposta.append(prop)
    
    municipal_utm['prop_sobreposta'] = proporcao_sobreposta
    
    # Remover segmentos com mais de 50% sobreposto
    LIMIAR_REMOCAO = 0.5
    mascara_manter = municipal_utm['prop_sobreposta'] < LIMIAR_REMOCAO
    
    removidos = (~mascara_manter).sum()
    mantidos = mascara_manter.sum()
    
    print(f"\n  Segmentos com >50% sobreposição (removidos): {removidos:,}")
    print(f"  Segmentos mantidos: {mantidos:,}")
    
    # Filtrar
    municipal_filtrado = municipal_utm[mascara_manter].copy()
    
    # Reprojetar de volta para WGS84
    municipal_filtrado = municipal_filtrado.to_crs(epsg=4326)
    
    # Remover coluna temporária
    municipal_filtrado = municipal_filtrado.drop(columns=['prop_sobreposta'])
    
    # Recalcular comprimento
    municipal_filtrado_utm = municipal_filtrado.to_crs(epsg=31983)
    municipal_filtrado['comprimento_m'] = municipal_filtrado_utm.geometry.length
    
    return municipal_filtrado, removidos


def analisar_conectividade(municipal, der):
    """
    Analisa a conectividade entre a malha municipal e o SRE
    
    Identifica:
    1. Pontos de conexão entre municipal e SRE
    2. Segmentos municipais desconectados
    """
    log_section("ETAPA 2: ANÁLISE DE CONECTIVIDADE")
    
    # Reprojetar para metros
    print("Reprojetando para sistema métrico...")
    municipal_utm = reprojetar_para_metros(municipal)
    der_utm = reprojetar_para_metros(der)
    
    # Filtrar SRE (estadual + federal)
    sre = der_utm[der_utm['Jurisdicao'].isin(['Estadual', 'Federal'])].copy()
    print(f"Segmentos SRE: {len(sre):,}")
    
    # Criar buffer ao redor do SRE para detectar conexões
    print(f"\nCriando buffer de conexão ({TOLERANCIA_CONEXAO}m)...")
    sre_buffer = unary_union(sre.geometry.buffer(TOLERANCIA_CONEXAO))
    
    # Identificar segmentos municipais que tocam o SRE
    print("Identificando segmentos conectados ao SRE...")
    municipal_utm = municipal_utm.reset_index(drop=True)
    
    conectado_sre = municipal_utm.geometry.intersects(sre_buffer)
    
    n_conectados = conectado_sre.sum()
    n_desconectados = (~conectado_sre).sum()
    
    print(f"\n  Segmentos diretamente conectados ao SRE: {n_conectados:,}")
    print(f"  Segmentos não conectados diretamente: {n_desconectados:,}")
    
    # Marcar conexão
    municipal_utm['conectado_sre'] = conectado_sre
    
    # Análise de componentes conexos (rede)
    print("\nAnalisando componentes da rede...")
    
    # Extrair endpoints de cada linha
    def get_endpoints(geom):
        if isinstance(geom, LineString):
            coords = list(geom.coords)
            return [Point(coords[0]), Point(coords[-1])]
        elif isinstance(geom, MultiLineString):
            endpoints = []
            for line in geom.geoms:
                coords = list(line.coords)
                endpoints.extend([Point(coords[0]), Point(coords[-1])])
            return endpoints
        return []
    
    # Criar grafo simplificado baseado em proximidade de endpoints
    print("Construindo grafo de conectividade...")
    
    # Coletar todos os endpoints
    all_endpoints = []
    for idx, row in municipal_utm.iterrows():
        eps = get_endpoints(row.geometry)
        for ep in eps:
            all_endpoints.append({
                'geometry': ep,
                'segment_idx': idx,
                'conectado_sre': row['conectado_sre']
            })
    
    endpoints_gdf = gpd.GeoDataFrame(all_endpoints, crs=municipal_utm.crs)
    print(f"  Total de endpoints: {len(endpoints_gdf):,}")
    
    # Contar segmentos conectados vs desconectados por highway
    print("\n  Conectividade por tipo de highway:")
    for hw in municipal_utm['highway'].unique():
        subset = municipal_utm[municipal_utm['highway'] == hw]
        conn = subset['conectado_sre'].sum()
        total = len(subset)
        pct = 100 * conn / total if total > 0 else 0
        print(f"    {hw}: {conn:,}/{total:,} conectados ({pct:.1f}%)")
    
    # Extensão conectada vs desconectada
    ext_conectada = municipal_utm[municipal_utm['conectado_sre']]['comprimento_m'].sum() / 1000
    ext_desconectada = municipal_utm[~municipal_utm['conectado_sre']]['comprimento_m'].sum() / 1000
    
    print(f"\n  Extensão diretamente conectada ao SRE: {ext_conectada:,.1f} km")
    print(f"  Extensão não conectada diretamente: {ext_desconectada:,.1f} km")
    
    # Reprojetar resultado de volta
    municipal_conectividade = municipal_utm.to_crs(epsg=4326)
    
    return municipal_conectividade, {
        'conectados': n_conectados,
        'desconectados': n_desconectados,
        'ext_conectada_km': ext_conectada,
        'ext_desconectada_km': ext_desconectada
    }


def extrair_pontos_conexao(municipal, der):
    """
    Extrai os pontos onde a malha municipal se conecta ao SRE
    """
    log_section("ETAPA 3: EXTRAÇÃO DE PONTOS DE CONEXÃO")
    
    # Reprojetar
    municipal_utm = reprojetar_para_metros(municipal)
    der_utm = reprojetar_para_metros(der)
    
    # SRE
    sre = der_utm[der_utm['Jurisdicao'].isin(['Estadual', 'Federal'])]
    
    # Encontrar interseções
    print("Identificando pontos de conexão...")
    
    pontos_conexao = []
    
    # Para cada segmento municipal conectado
    municipais_conectados = municipal_utm[municipal_utm['conectado_sre'] == True]
    
    for idx, mun_row in municipais_conectados.iterrows():
        for _, sre_row in sre.iterrows():
            try:
                intersecao = mun_row.geometry.intersection(sre_row.geometry)
                if not intersecao.is_empty:
                    # Extrair centroide da interseção como ponto de conexão
                    if intersecao.geom_type == 'Point':
                        pontos_conexao.append({
                            'geometry': intersecao,
                            'rodovia_sre': sre_row.get('Rodovia', 'N/A'),
                            'highway_municipal': mun_row['highway']
                        })
                    elif intersecao.geom_type in ['MultiPoint', 'GeometryCollection']:
                        for geom in intersecao.geoms:
                            if geom.geom_type == 'Point':
                                pontos_conexao.append({
                                    'geometry': geom,
                                    'rodovia_sre': sre_row.get('Rodovia', 'N/A'),
                                    'highway_municipal': mun_row['highway']
                                })
            except:
                continue
    
    print(f"  Pontos de conexão encontrados: {len(pontos_conexao):,}")
    
    if pontos_conexao:
        pontos_gdf = gpd.GeoDataFrame(pontos_conexao, crs=municipal_utm.crs)
        pontos_gdf = pontos_gdf.to_crs(epsg=4326)
        return pontos_gdf
    
    return None


def salvar_resultados(municipal_final, stats_conectividade, removidos):
    """Salva os resultados finais"""
    log_section("SALVANDO RESULTADOS")
    
    # Arquivo principal
    output_file = OUTPUT_DIR / 'malha_municipal_sp_refinada.gpkg'
    print(f"Salvando malha refinada: {output_file}")
    municipal_final.to_file(output_file, driver='GPKG')
    
    # Separar conectados e desconectados
    conectados = municipal_final[municipal_final['conectado_sre'] == True]
    desconectados = municipal_final[municipal_final['conectado_sre'] == False]
    
    # Salvar separadamente
    output_conectados = INTERMEDIARIO_DIR / 'malha_municipal_conectada_sre.gpkg'
    output_desconectados = INTERMEDIARIO_DIR / 'malha_municipal_desconectada_sre.gpkg'
    
    print(f"Salvando conectados: {output_conectados}")
    conectados.to_file(output_conectados, driver='GPKG')
    
    print(f"Salvando desconectados: {output_desconectados}")
    desconectados.to_file(output_desconectados, driver='GPKG')
    
    # Relatório
    relatorio_file = RELATORIO_DIR / 'relatorio_refinamento_conectividade.txt'
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE REFINAMENTO E CONECTIVIDADE\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("SUBTRAÇÃO DA MALHA DER\n")
        f.write("-"*40 + "\n")
        f.write(f"Segmentos removidos (sobreposição >50%): {removidos:,}\n")
        f.write(f"Segmentos restantes: {len(municipal_final):,}\n\n")
        
        f.write("ANÁLISE DE CONECTIVIDADE\n")
        f.write("-"*40 + "\n")
        f.write(f"Diretamente conectados ao SRE: {stats_conectividade['conectados']:,}\n")
        f.write(f"Não conectados diretamente: {stats_conectividade['desconectados']:,}\n")
        f.write(f"Extensão conectada: {stats_conectividade['ext_conectada_km']:,.1f} km\n")
        f.write(f"Extensão desconectada: {stats_conectividade['ext_desconectada_km']:,.1f} km\n\n")
        
        f.write("DISTRIBUIÇÃO POR HIGHWAY\n")
        f.write("-"*40 + "\n")
        f.write(municipal_final['highway'].value_counts().to_string())
        f.write("\n\nExtensão total: ")
        f.write(f"{municipal_final['comprimento_m'].sum()/1000:,.1f} km\n")
    
    print(f"Relatório salvo: {relatorio_file}")
    
    return output_file


def main():
    print("="*60)
    print("REFINAMENTO DA MALHA MUNICIPAL - SUBTRAÇÃO DER + CONECTIVIDADE")
    print("="*60)
    
    # 1. Carregar dados
    municipal, der = carregar_dados()
    
    # 2. Subtrair malha DER
    municipal_subtraido, removidos = subtrair_malha_der(municipal, der)
    
    print(f"\nApós subtração DER:")
    print(f"  Segmentos: {len(municipal_subtraido):,}")
    print(f"  Extensão: {municipal_subtraido['comprimento_m'].sum()/1000:,.1f} km")
    
    # 3. Analisar conectividade
    municipal_conectividade, stats = analisar_conectividade(municipal_subtraido, der)
    
    # 4. Salvar resultados
    output = salvar_resultados(municipal_conectividade, stats, removidos)
    
    # Resumo final
    log_section("RESUMO FINAL")
    print(f"Malha municipal refinada: {len(municipal_conectividade):,} segmentos")
    print(f"Extensão total: {municipal_conectividade['comprimento_m'].sum()/1000:,.1f} km")
    print(f"Conectados ao SRE: {stats['conectados']:,} ({100*stats['conectados']/len(municipal_conectividade):.1f}%)")
    print(f"Arquivo gerado: {output}")
    print("\n✅ Processamento concluído!")
    
    return municipal_conectividade


if __name__ == "__main__":
    resultado = main()
