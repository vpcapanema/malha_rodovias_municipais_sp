#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERAR RELATÓRIO PARCIAL - com dados coletados até agora
Relatório em HTML mostrando:
- Municípios pesquisados
- Taxa de sucesso
- Dados encontrados
- Status geral
"""

import json
from pathlib import Path
from datetime import datetime

def gerar_relatorio_html_final():
    """Gera relatório HTML final com dados coletados"""
    
    progresso_file = Path("pesquisa_dados/progresso/progresso.json")
    
    if not progresso_file.exists():
        print("Nenhum progresso encontrado!")
        return
    
    with open(progresso_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    resultados = stats['resultados']
    total_munis = stats['total_municipios']
    total_buscas = stats['total_buscas']
    sucesso = stats['sucesso']
    falha = stats['falha']
    dados_encontrados_count = stats['dados_encontrados']
    
    munis_com_dados = [r for r in resultados if r['status'] == 'acessado']
    
    # Calcular percentagens
    taxa_sucesso = (sucesso / max(total_buscas, 1)) * 100
    taxa_falha = (falha / max(total_buscas, 1)) * 100
    taxa_munis_dados = (len(munis_com_dados) / max(total_munis, 1)) * 100
    
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnóstico Pesquisa Malha Viária - 645 Municípios SP</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            padding: 40px;
        }}
        .header {{
            background: linear-gradient(135deg, #1a4d7a 0%, #0f3460 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 40px;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 16px;
            opacity: 0.9;
            margin: 5px 0;
        }}
        .status-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            margin-top: 15px;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            border-left: 5px solid rgba(255,255,255,0.3);
        }}
        .stat-number {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-section {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 40px;
            border-left: 5px solid #667eea;
        }}
        .summary-section h2 {{
            color: #1a4d7a;
            margin-bottom: 20px;
            font-size: 24px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .metric {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            color: #666;
            font-weight: 500;
        }}
        .metric-value {{
            font-weight: bold;
            color: #1a4d7a;
            font-size: 20px;
            font-family: 'Courier New', monospace;
        }}
        .progress-bar {{
            width: 100%;
            height: 35px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #27ae60 0%, #2ecc71 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 40px;
        }}
        th {{
            background: #1a4d7a;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-right: 1px solid rgba(255,255,255,0.1);
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
            border-right: 1px solid #f0f0f0;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .status-badge-table {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 5px;
            font-size: 11px;
            font-weight: bold;
        }}
        .status-success {{
            background: #d4edda;
            color: #155724;
        }}
        .status-pending {{
            background: #fff3cd;
            color: #856404;
        }}
        .footer {{
            margin-top: 50px;
            padding: 25px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            text-align: center;
            color: #666;
            font-size: 13px;
            border-top: 3px solid #667eea;
        }}
        h2 {{
            color: #1a4d7a;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 26px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .warning {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            color: #856404;
        }}
        .success {{
            background: #d4edda;
            border: 2px solid #28a745;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            color: #155724;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Diagnóstico Pesquisa Malha Viária Municipal</h1>
            <p>Pesquisa Sistematizada em 645 Municípios de São Paulo</p>
            <p>Meta: Localizar bases de dados vetoriais da malha viária municipal</p>
            <div class="status-badge">
                ⏳ Pesquisa em Progresso - {(total_munis/645*100):.1f}% Concluído
            </div>
            <p style="margin-top: 15px; font-size: 12px;">Atualizado em: {datetime.now().strftime('%d de %B de %Y às %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_munis}</div>
                <div class="stat-label">Municípios Pesquisados</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(total_munis/645*100):.1f}%">{(total_munis/645*100):.0f}%</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_buscas}</div>
                <div class="stat-label">Total de Buscas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sucesso}</div>
                <div class="stat-label">Acessos Bem-Sucedidos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(munis_com_dados)}</div>
                <div class="stat-label">Municípios com Dados</div>
            </div>
        </div>
        
        <div class="summary-section">
            <h2>📊 Análise de Resultados</h2>
            
            <div class="metric">
                <span class="metric-label">Taxa de Sucesso de Acessos:</span>
                <div>
                    <span class="metric-value">{taxa_sucesso:.1f}%</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {taxa_sucesso:.0f}%; background: linear-gradient(90deg, #3498db 0%, #2980b9 100%)">{taxa_sucesso:.0f}%</div>
                    </div>
                </div>
            </div>
            
            <div class="metric">
                <span class="metric-label">Taxa de Falha:</span>
                <div>
                    <span class="metric-value" style="color: #e74c3c;">{taxa_falha:.1f}%</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {taxa_falha:.0f}%; background: linear-gradient(90deg, #e74c3c 0%, #c0392b 100%)">{taxa_falha:.0f}%</div>
                    </div>
                </div>
            </div>
            
            <div class="metric">
                <span class="metric-label">Taxa de Municípios com Dados:</span>
                <div>
                    <span class="metric-value" style="color: #27ae60;">{taxa_munis_dados:.1f}%</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {taxa_munis_dados:.0f}%">{taxa_munis_dados:.0f}%</div>
                    </div>
                </div>
            </div>
            
            <div class="metric">
                <span class="metric-label">Média de Buscas por Município:</span>
                <span class="metric-value">{(total_buscas / max(total_munis, 1)):.1f}</span>
            </div>
        </div>
        
        <h2>📋 Municípios com Dados Encontrados ({len(munis_com_dados)})</h2>
        
        {f'<div class="success">✓ Sucesso! Encontrados dados em {len(munis_com_dados)} municípios</div>' if munis_com_dados else '<div class="warning">⚠ Nenhum dado encontrado ainda nesta fase</div>'}
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Município</th>
                    <th>Buscas OK</th>
                    <th>Termos Encontrados</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Adicionar municípios com dados
    for resultado in munis_com_dados[:50]:
        buscas_total = len(resultado['buscas'])
        buscas_sucesso = sum(1 for b in resultado['buscas'] if b['status'] == 'sucesso')
        dados_encontrados = sum(1 for b in resultado['buscas'] if b['conteudo_encontrado'])
        termos = []
        for b in resultado['buscas']:
            if b['dados_encontrados']:
                termos.extend(b['dados_encontrados'])
        termos = list(set(termos))
        
        html += f"""
                <tr>
                    <td><strong>{resultado['id']}</strong></td>
                    <td>{resultado['nome']}</td>
                    <td>{buscas_sucesso}/{buscas_total}</td>
                    <td>{', '.join(termos[:3])}</td>
                    <td><span class="status-badge-table status-success">✓ Acessado</span></td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <h2>📈 Progresso da Pesquisa</h2>
        
        <table>
            <thead>
                <tr>
                    <th>Métrica</th>
                    <th>Valor</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Municípios Processados</td>
                    <td>""" + f"{total_munis}/645" + """</td>
                    <td><span class="status-badge-table status-pending">⏳ Em Progresso</span></td>
                </tr>
                <tr>
                    <td>Estimativa de Conclusão</td>
                    <td>""" + f"~{int(645 / max(total_munis, 1) * 5)} minutos" + """</td>
                    <td><span class="status-badge-table">ℹ Estimado</span></td>
                </tr>
                <tr>
                    <td>Arquivos de Saída</td>
                    <td>pesquisa_dados/relatorios/</td>
                    <td><span class="status-badge-table status-success">✓ Disponível</span></td>
                </tr>
            </tbody>
        </table>
        
        <div class="footer">
            <h3 style="color: #1a4d7a; margin-bottom: 10px;">📌 Informações da Pesquisa</h3>
            <p><strong>Objetivo:</strong> Localizar e catalogar bases de dados vetoriais (shapefile, GeoPackage, GeoJSON) da malha viária municipal em todos os 645 municípios de São Paulo</p>
            <p style="margin-top: 10px;"><strong>Metodologia:</strong> Busca sistemática em portais de dados abertos, SIG municipal e secretarias de obras/planejamento</p>
            <p style="margin-top: 10px;"><strong>Termos de Busca:</strong> malha viária, rede viária, shapefile, geopackage, geojson, cartografia, SIG, dados abertos</p>
            <p style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 15px;">
                <strong>Relatório Gerado:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
                <strong>Status:</strong> ⏳ Pesquisa em Andamento ({(total_munis/645*100):.1f}% Concluído)<br>
                <strong>Próxima Atualização:</strong> Em tempo real enquanto a pesquisa continua
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    arquivo = Path("pesquisa_dados/relatorios/diagnostico_ATUAL.html")
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Relatório gerado: {arquivo}")
    print(f"  Total de municípios processados: {total_munis}/645")
    print(f"  Taxa de sucesso: {taxa_sucesso:.1f}%")
    print(f"  Municípios com dados: {len(munis_com_dados)}")
    print(f"  Progresso: {(total_munis/645*100):.1f}%")
    
    return arquivo

if __name__ == "__main__":
    gerar_relatorio_html_final()
