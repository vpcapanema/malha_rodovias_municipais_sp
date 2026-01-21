#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PESQUISA COMPLETA - TODOS OS 645 MUNICÍPIOS DE SÃO PAULO
Fonte oficial: IBGE
Executa: python PESQUISA_645_IBGE.py
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from LISTA_645_MUNICIPIOS_SP import MUNICIPIOS_SP_645

class PesquisadorMalhaViaria:
    """Pesquisador de malha viária municipal"""
    
    def __init__(self, diretorio_base="pesquisa_dados"):
        self.diretorio_base = Path(diretorio_base)
        self.diretorio_base.mkdir(exist_ok=True)
        
        self.dir_downloads = self.diretorio_base / "dados_encontrados"
        self.dir_relatorios = self.diretorio_base / "relatorios"
        self.dir_logs = self.diretorio_base / "logs"
        self.dir_progresso = self.diretorio_base / "progresso"
        
        for d in [self.dir_downloads, self.dir_relatorios, self.dir_logs, self.dir_progresso]:
            d.mkdir(exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.stats = {
            "total_municipios": 0,
            "municipios_processados": 0,
            "total_buscas": 0,
            "sucesso": 0,
            "falha": 0,
            "dados_encontrados": 0,
            "resultados": [],
            "timestamp_inicio": datetime.now().isoformat()
        }
        
        self.termos_busca = [
            "malha viária", "malha viaria", "rede viária", "rede viaria",
            "shapefile", "geojson", "geopackage", "gpkg",
            "mapa logradouros", "base cartografica", "cartografia",
            "dados geograficos", "SIG", "GIS", "geodados",
            "vias publicas", "sistema viario", "dados abertos", "portal dados"
        ]
        
        self.arquivo_progresso = self.dir_progresso / "progresso_645.json"
    
    def salvar_progresso(self):
        """Salva progresso atual"""
        with open(self.arquivo_progresso, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def carregar_progresso(self):
        """Carrega progresso anterior se existir"""
        if self.arquivo_progresso.exists():
            with open(self.arquivo_progresso, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def normalizar_nome(self, municipio):
        """Normaliza nome do município para URL"""
        import unicodedata
        nome = unicodedata.normalize('NFKD', municipio.lower())
        nome = nome.encode('ascii', 'ignore').decode('ascii')
        nome = nome.replace(' ', '').replace("'", "").replace("-", "")
        return nome
    
    def tentar_acesso_url(self, url, timeout=5):
        """Tenta acessar URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception:
            return None
    
    def _gerar_urls_busca(self, municipio):
        """Gera URLs de busca para um município"""
        nome_url = self.normalizar_nome(municipio)
        
        return {
            "site_oficial": f"https://{nome_url}.sp.gov.br",
            "portal_dados": f"https://{nome_url}.sp.gov.br/dados",
            "secretaria_obras": f"https://{nome_url}.sp.gov.br/secretaria-de-obras"
        }
    
    def _analisar_conteudo(self, conteudo, municipio):
        """Analisa conteúdo buscando termos relacionados"""
        encontrados = []
        conteudo_lower = conteudo.lower()
        
        for termo in self.termos_busca:
            if termo.lower() in conteudo_lower:
                encontrados.append(termo)
        
        return encontrados
    
    def pesquisar_municipio(self, municipio_nome, municipio_id):
        """Pesquisa um município"""
        resultado = {
            "id": municipio_id,
            "nome": municipio_nome,
            "timestamp": datetime.now().isoformat(),
            "buscas": [],
            "dados_encontrados": [],
            "status": "pendente"
        }
        
        urls_busca = self._gerar_urls_busca(municipio_nome)
        
        for tipo_busca, url in urls_busca.items():
            self.stats["total_buscas"] += 1
            
            resultado_busca = {
                "tipo": tipo_busca,
                "url": url,
                "status": "falha",
                "conteudo_encontrado": False,
                "termos_encontrados": []
            }
            
            conteudo = self.tentar_acesso_url(url)
            
            if conteudo:
                self.stats["sucesso"] += 1
                resultado_busca["status"] = "sucesso"
                
                termos = self._analisar_conteudo(conteudo, municipio_nome)
                if termos:
                    resultado_busca["conteudo_encontrado"] = True
                    resultado_busca["termos_encontrados"] = termos
                    resultado["dados_encontrados"].extend(termos)
            else:
                self.stats["falha"] += 1
            
            resultado["buscas"].append(resultado_busca)
            time.sleep(0.2)
        
        if resultado["dados_encontrados"]:
            resultado["status"] = "dados_encontrados"
            self.stats["dados_encontrados"] += 1
        elif any(b["status"] == "sucesso" for b in resultado["buscas"]):
            resultado["status"] = "acessado"
        else:
            resultado["status"] = "inacessivel"
        
        self.stats["resultados"].append(resultado)
        self.stats["municipios_processados"] += 1
        
        return resultado
    
    def gerar_relatorio_html(self):
        """Gera relatório HTML"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = self.dir_relatorios / f"diagnostico_645_{timestamp}.html"
        
        taxa_sucesso = (self.stats['sucesso'] / max(self.stats['total_buscas'], 1)) * 100
        progresso = (self.stats['municipios_processados'] / 645) * 100
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Diagnóstico - Pesquisa Malha Viária SP (645 Municípios IBGE)</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-box.success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-box.warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .stat-box.info {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        .progress-bar {{ background: #ecf0f1; border-radius: 10px; height: 30px; margin: 20px 0; overflow: hidden; }}
        .progress-fill {{ background: linear-gradient(90deg, #11998e, #38ef7d); height: 100%; transition: width 0.5s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .status-ok {{ color: #27ae60; font-weight: bold; }}
        .status-fail {{ color: #e74c3c; }}
        .fonte {{ background: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗺️ Diagnóstico - Pesquisa Malha Viária Municipal SP</h1>
        
        <div class="fonte">
            <strong>📊 Fonte Oficial:</strong> IBGE - Instituto Brasileiro de Geografia e Estatística<br>
            <strong>🔢 Total de Municípios:</strong> 645 (lista completa oficial)
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progresso:.1f}%">{progresso:.1f}% Concluído ({self.stats['municipios_processados']}/645)</div>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{self.stats['municipios_processados']}</div>
                <div class="stat-label">Municípios Processados</div>
            </div>
            <div class="stat-box info">
                <div class="stat-value">{self.stats['total_buscas']}</div>
                <div class="stat-label">Total de Buscas</div>
            </div>
            <div class="stat-box success">
                <div class="stat-value">{self.stats['sucesso']}</div>
                <div class="stat-label">Acessos com Sucesso</div>
            </div>
            <div class="stat-box warning">
                <div class="stat-value">{self.stats['dados_encontrados']}</div>
                <div class="stat-label">Com Dados Encontrados</div>
            </div>
        </div>
        
        <h2>📈 Estatísticas</h2>
        <ul>
            <li><strong>Taxa de Sucesso:</strong> {taxa_sucesso:.1f}%</li>
            <li><strong>Buscas por Município:</strong> 3 (site oficial, portal dados, secretaria obras)</li>
            <li><strong>Início:</strong> {self.stats.get('timestamp_inicio', 'N/A')}</li>
        </ul>
        
        <h2>📋 Resultados por Município</h2>
        <table>
            <tr>
                <th>#</th>
                <th>Município</th>
                <th>Status</th>
                <th>Termos Encontrados</th>
            </tr>
"""
        
        for r in self.stats['resultados'][-50:]:
            status_class = "status-ok" if r['status'] == 'dados_encontrados' else ("status-ok" if r['status'] == 'acessado' else "status-fail")
            termos = ", ".join(set(r.get('dados_encontrados', [])))[:50]
            html += f"""
            <tr>
                <td>{r['id']}</td>
                <td>{r['nome']}</td>
                <td class="{status_class}">{r['status']}</td>
                <td>{termos or '-'}</td>
            </tr>
"""
        
        html += """
        </table>
        
        <p style="margin-top: 30px; color: #7f8c8d; text-align: center;">
            Gerado em: """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """ | Fonte: IBGE
        </p>
    </div>
</body>
</html>
"""
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Copiar para arquivo atual
        atual = self.dir_relatorios / "diagnostico_645_ATUAL.html"
        with open(atual, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return arquivo


def main():
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║   PESQUISA COMPLETA - TODOS OS 645 MUNICÍPIOS DE SÃO PAULO                ║
║                    Fonte Oficial: IBGE                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

Total de municípios a pesquisar: {len(MUNICIPIOS_SP_645)}
Início: {datetime.now().strftime('%H:%M:%S')}
""")
    
    pesquisador = PesquisadorMalhaViaria()
    pesquisador.stats["total_municipios"] = len(MUNICIPIOS_SP_645)
    
    # Verificar progresso anterior
    progresso_anterior = pesquisador.carregar_progresso()
    inicio = 0
    
    if progresso_anterior:
        inicio = progresso_anterior.get("municipios_processados", 0)
        if inicio > 0 and inicio < len(MUNICIPIOS_SP_645):
            pesquisador.stats = progresso_anterior
            print(f"Retomando de {inicio}...")
    
    try:
        for i, municipio in enumerate(MUNICIPIOS_SP_645[inicio:], start=inicio+1):
            try:
                resultado = pesquisador.pesquisar_municipio(municipio, i)
                
                status_icon = "✓" if resultado['status'] in ['acessado', 'dados_encontrados'] else "✗"
                print(f"[{i:3d}/645] {status_icon} {municipio:30s}", end="")
                
                if i % 10 == 0:
                    pesquisador.salvar_progresso()
                    taxa = (pesquisador.stats['sucesso'] / max(pesquisador.stats['total_buscas'], 1)) * 100
                    print(f" | Sucesso: {taxa:.1f}%")
                else:
                    print()
                    
            except Exception as e:
                print(f"[{i:3d}/645] ✗ {municipio:30s} ERRO: {str(e)[:30]}")
        
        # Salvar final
        pesquisador.salvar_progresso()
        relatorio = pesquisador.gerar_relatorio_html()
        
        print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                          PESQUISA CONCLUÍDA!                              ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 RESULTADOS FINAIS:
   • Municípios processados: {pesquisador.stats['municipios_processados']}/645
   • Total de buscas: {pesquisador.stats['total_buscas']}
   • Acessos com sucesso: {pesquisador.stats['sucesso']}
   • Municípios com dados: {pesquisador.stats['dados_encontrados']}
   • Taxa de sucesso: {(pesquisador.stats['sucesso'] / max(pesquisador.stats['total_buscas'], 1)) * 100:.1f}%

📁 Arquivos gerados:
   • Progresso: pesquisa_dados/progresso/progresso_645.json
   • Relatório: {relatorio}
""")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário. Salvando progresso...")
        pesquisador.salvar_progresso()
        print("✅ Progresso salvo. Execute novamente para continuar.")


if __name__ == "__main__":
    main()
