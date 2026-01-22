"""
Script para baixar dados populacionais do IBGE para municípios de SP
Fonte: API SIDRA - Tabela 6579 (Estimativas Populacionais)
"""

import requests
import json
from pathlib import Path
import pandas as pd

def baixar_populacao_sp_completo():
    """
    Baixa população de TODOS os municípios de SP de uma vez
    Usando API SIDRA com filtro por UF
    """
    print("[API] Buscando dados populacionais de SP no IBGE SIDRA...")
    print("=" * 60)
    
    try:
        # API SIDRA - Todos municípios de SP, população mais recente
        # Tabela 6579: Estimativa da população
        # Variável 9324: População residente estimada
        # Período: last 1 (mais recente disponível)
        url = "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last%201"
        
        print(f"[REQUEST] {url}")
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[ERRO] Status code: {response.status_code}")
            return []
        
        data = response.json()
        print(f"[OK] {len(data)} registros recebidos")
        
        # Filtrar apenas municípios de SP (código começa com 35)
        municipios_sp = []
        
        for i, registro in enumerate(data):
            if i == 0:  # Pular cabeçalho
                continue
            
            cod_ibge = registro.get('D1C', '')
            nome = registro.get('D1N', '')
            valor = registro.get('V', '')
            ano = registro.get('D3N', '')
            
            # Filtrar por SP (código IBGE começa com 35)
            if cod_ibge.startswith('35') and valor and valor != '...':
                # Remover " - SP" do nome se existir
                nome_limpo = nome.replace(' - SP', '')
                
                municipios_sp.append({
                    'cod_ibge': cod_ibge,
                    'municipio': nome_limpo,
                    'populacao': int(valor),
                    'ano_referencia': ano,
                    'fonte': 'IBGE SIDRA - Tabela 6579'
                })
        
        print(f"[FILTRO] {len(municipios_sp)} municipios de SP encontrados (ano {ano if municipios_sp else 'N/A'})")
        
        return municipios_sp
        
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados: {e}")
        return []

def carregar_municipios_existentes():
    """Carrega códigos IBGE dos municípios já processados"""
    arquivo_json = Path("docs/data/municipios_indicadores.json")
    
    if arquivo_json.exists():
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {str(m['Cod_ibge']): m['Municipio'] for m in data}
    
    # Alternativa: ler do GeoJSON
    arquivo_geojson = Path("docs/data/municipios_totais.geojson")
    with open(arquivo_geojson, 'r', encoding='utf-8') as f:
        data = json.load(f)
        municipios = {}
        for feat in data['features']:
            cod = feat['properties'].get('Cod_ibge') or feat['properties'].get('cod_ibge')
            nome = feat['properties'].get('Municipio') or feat['properties'].get('municipio')
            if cod:
                municipios[str(cod)] = nome
        return municipios

def processar_dados():
    """Processa e cruza dados do IBGE com municípios locais"""
    print("\n[PROCESSO] Integrando dados...")
    print("=" * 60)
    
    # 1. Baixar dados do IBGE
    dados_ibge = baixar_populacao_sp_completo()
    
    if not dados_ibge:
        print("[ERRO] Nenhum dado foi baixado do IBGE")
        return
    
    # 2. Carregar municípios locais
    municipios_locais = carregar_municipios_existentes()
    print(f"[LOCAL] {len(municipios_locais)} municipios no banco local")
    
    # 3. Fazer merge por código IBGE
    resultados = []
    encontrados = 0
    nao_encontrados = []
    
    for cod_ibge, nome_local in municipios_locais.items():
        # Buscar nos dados do IBGE
        dado_ibge = next((d for d in dados_ibge if d['cod_ibge'] == cod_ibge), None)
        
        if dado_ibge:
            resultados.append(dado_ibge)
            encontrados += 1
        else:
            nao_encontrados.append((cod_ibge, nome_local))
    
    print(f"[MATCH] {encontrados}/{len(municipios_locais)} municipios encontrados")
    
    if nao_encontrados:
        print(f"[ALERTA] {len(nao_encontrados)} municipios sem dados:")
        for cod, nome in nao_encontrados[:10]:
            print(f"  - {nome} ({cod})")
        if len(nao_encontrados) > 10:
            print(f"  ... e mais {len(nao_encontrados) - 10}")
    
    # 4. Salvar resultados
    output_file = Path("docs/data/populacao_ibge.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SALVO] Dados salvos em: {output_file}")
    
    # 5. Estatísticas
    if resultados:
        pops = [r['populacao'] for r in resultados]
        print(f"\n[STATS] Estatisticas:")
        print(f"  - Ano: {resultados[0]['ano_referencia']}")
        print(f"  - Populacao total: {sum(pops):,} habitantes")
        print(f"  - Media: {sum(pops)//len(pops):,} hab/municipio")
        print(f"  - Minimo: {min(pops):,} habitantes")
        print(f"  - Maximo: {max(pops):,} habitantes")
    
    return resultados

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DOWNLOAD DE DADOS POPULACIONAIS - IBGE")
    print("="*60 + "\n")
    
    resultados = processar_dados()
    
    print("\n" + "="*60)
    print("[CONCLUIDO] Processo finalizado")
    print("="*60)
