#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUSCA SISTEMATIZADA - MALHA VIÁRIA MUNICIPAL SÃO PAULO
Percorre sites de prefeituras municipais em busca de dados vetoriais
Data: 15/01/2026
"""

import os
import json
import time
import requests
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup

class PesquisadorMalhaViaria:
    """Classe para pesquisar malha viária nos sites municipais"""
    
    def __init__(self, diretorio_base="pesquisa_dados"):
        self.diretorio_base = Path(diretorio_base)
        self.diretorio_base.mkdir(exist_ok=True)
        
        # Diretórios para organização
        self.dir_downloads = self.diretorio_base / "dados_encontrados"
        self.dir_relatorios = self.diretorio_base / "relatorios"
        self.dir_logs = self.diretorio_base / "logs"
        
        for d in [self.dir_downloads, self.dir_relatorios, self.dir_logs]:
            d.mkdir(exist_ok=True)
        
        # Headers para requisições
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Estatísticas
        self.stats = {
            "total_municipios": 0,
            "total_buscas": 0,
            "sucesso": 0,
            "falha": 0,
            "dados_encontrados": 0,
            "resultados": []
        }
        
        # Termos de busca para malha viária
        self.termos_busca = [
            "malha viária", "malha viaria", "rede viária", "rede viaria",
            "shapefile", "geojson", "geopackage", "gpkg",
            "mapa logradouros", "base cartografica", "cartografia",
            "dados geograficos", "SIG", "GIS", "geodados",
            "vias publicas", "sistema viario", "sistema viario",
            "open data", "dados abertos", "portal dados"
        ]
    
    def tentar_acesso_url(self, url, timeout=5):
        """Tenta acessar URL e retorna conteúdo"""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as e:
            print(f"Erro ao acessar {url}: {str(e)}")
            return None
    
    def pesquisar_municipio(self, municipio_nome, municipio_id):
        """Realiza pesquisa completa para um município"""
        print(f"\n{'='*80}")
        print(f"MUNICÍPIO [{municipio_id}]: {municipio_nome}")
        print(f"{'='*80}")
        
        resultado = {
            "id": municipio_id,
            "nome": municipio_nome,
            "timestamp": datetime.now().isoformat(),
            "buscas": [],
            "dados_encontrados": [],
            "status": "pendente"
        }
        
        # Gerar URLs a pesquisar
        urls_busca = self._gerar_urls_busca(municipio_nome)
        
        # Executar buscas
        for tipo_busca, url in urls_busca.items():
            print(f"\n  [{tipo_busca}] {url}")
            self.stats["total_buscas"] += 1
            
            resultado_busca = {
                "tipo": tipo_busca,
                "url": url,
                "status": "falha",
                "conteudo_encontrado": False,
                "dados_encontrados": []
            }
            
            # Tentar acessar
            conteudo = self.tentar_acesso_url(url)
            
            if conteudo:
                print(f"    ✓ Acessado com sucesso (tamanho: {len(conteudo)} bytes)")
                resultado_busca["status"] = "sucesso"
                self.stats["sucesso"] += 1
                
                # Analisar conteúdo em busca de termos
                achados = self._analisar_conteudo(conteudo, municipio_nome)
                if achados:
                    print(f"    → Encontrados termos: {', '.join(achados)}")
                    resultado_busca["conteudo_encontrado"] = True
                    resultado_busca["dados_encontrados"] = achados
                    self.stats["dados_encontrados"] += 1
            else:
                print(f"    ✗ Erro ao acessar")
                self.stats["falha"] += 1
            
            resultado["buscas"].append(resultado_busca)
            time.sleep(0.5)  # Respeitar servidores
        
        # Determinar status final
        if any(b["status"] == "sucesso" for b in resultado["buscas"]):
            resultado["status"] = "acessado"
        
        self.stats["resultados"].append(resultado)
        return resultado
    
    def _gerar_urls_busca(self, municipio):
        """Gera lista de URLs para pesquisa em um município"""
        nome_slug = municipio.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ã", "a").replace("õ", "o").replace("ç", "c")
        
        urls = {
            "site_oficial": f"https://{nome_slug}.sp.gov.br",
            "portal_dados": f"https://{nome_slug}.sp.gov.br/dados",
            "portal_dados_alt": f"https://{nome_slug}.sp.gov.br/open-data",
            "secretaria_obras": f"https://{nome_slug}.sp.gov.br/secretaria-de-obras",
            "secretaria_planejamento": f"https://{nome_slug}.sp.gov.br/secretaria-de-planejamento",
            "sig_municipal": f"https://{nome_slug}.sp.gov.br/sig",
            "geoserver": f"https://geo.{nome_slug}.sp.gov.br",
        }
        
        return urls
    
    def _analisar_conteudo(self, conteudo, municipio):
        """Analisa conteúdo em busca de termos relacionados"""
        conteudo_lower = conteudo.lower()
        encontrados = []
        
        for termo in self.termos_busca:
            if termo.lower() in conteudo_lower:
                encontrados.append(termo)
        
        return list(set(encontrados))  # Remove duplicatas
    
    def gerar_relatorio_html(self):
        """Gera relatório HTML com diagnóstico"""
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório - Pesquisa Malha Viária Municipal SP</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #1a4d7a;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
            color: #1a4d7a;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            margin-top: 20px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #1a4d7a;
            color: white;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .sucesso {{
            color: #27ae60;
            font-weight: bold;
        }}
        .falha {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .percentage {{
            font-size: 14px;
            color: #666;
        }}
        .footer {{
            margin-top: 30px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Relatório de Pesquisa - Malha Viária Municipal São Paulo</h1>
        <p>Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{self.stats['total_municipios']}</div>
            <div class="stat-label">Municípios Pesquisados</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{self.stats['total_buscas']}</div>
            <div class="stat-label">Total de Buscas</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{self.stats['sucesso']}</div>
            <div class="stat-label">Acessos com Sucesso</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{self.stats['dados_encontrados']}</div>
            <div class="stat-label">Munics. com Dados</div>
        </div>
    </div>
    
    <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h3>📈 Estatísticas Gerais</h3>
        <p><strong>Taxa de Sucesso:</strong> <span class="percentage">{(self.stats['sucesso'] / max(self.stats['total_buscas'], 1) * 100):.1f}%</span></p>
        <p><strong>Taxa de Falha:</strong> <span class="percentage">{(self.stats['falha'] / max(self.stats['total_buscas'], 1) * 100):.1f}%</span></p>
        <p><strong>Taxa de Municípios com Dados:</strong> <span class="percentage">{(self.stats['dados_encontrados'] / max(self.stats['total_municipios'], 1) * 100):.1f}%</span></p>
    </div>
    
    <h3>📋 Detalhes por Município</h3>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Município</th>
                <th>Buscas Realizadas</th>
                <th>Acessos Bem-Sucedidos</th>
                <th>Dados Encontrados</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
"""
        
        # Adicionar linhas da tabela
        for resultado in self.stats['resultados']:
            buscas_total = len(resultado['buscas'])
            buscas_sucesso = sum(1 for b in resultado['buscas'] if b['status'] == 'sucesso')
            dados_encontrados = sum(1 for b in resultado['buscas'] if b['conteudo_encontrado'])
            
            status_class = 'sucesso' if resultado['status'] == 'acessado' else 'falha'
            status_icon = '✓' if resultado['status'] == 'acessado' else '✗'
            
            html_content += f"""
            <tr>
                <td>{resultado['id']}</td>
                <td>{resultado['nome']}</td>
                <td>{buscas_sucesso}/{buscas_total}</td>
                <td class="{status_class}">{buscas_sucesso}</td>
                <td>{dados_encontrados}</td>
                <td class="{status_class}">{status_icon}</td>
            </tr>
"""
        
        html_content += """
        </tbody>
    </table>
    
    <div class="footer">
        <p><strong>Nota:</strong> Este relatório documenta a pesquisa sistematizada em portais municipais.</p>
        <p>Diretório de dados: pesquisa_dados/dados_encontrados/</p>
    </div>
</body>
</html>
"""
        
        # Salvar arquivo
        arquivo_relatorio = self.dir_relatorios / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ Relatório salvo em: {arquivo_relatorio}")
        return arquivo_relatorio

if __name__ == "__main__":
    pesquisador = PesquisadorMalhaViaria()
    print("Iniciando pesquisa sistematizada...")
