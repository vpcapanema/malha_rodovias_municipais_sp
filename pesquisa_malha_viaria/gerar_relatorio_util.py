#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório ÚTIL - Informações Concretas e Acionáveis
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

# Caminhos
PROGRESSO_FILE = Path("pesquisa_dados/progresso/progresso_645.json")
OUTPUT_DIR = Path("pesquisa_dados/relatorios")

# Termos por prioridade (mais específicos = mais úteis)
TERMOS_ALTA_PRIORIDADE = ['shapefile', 'shp', 'geojson', 'geopackage', 'gpkg', 'kml', 'kmz', 'dwg', 'dxf']
TERMOS_MEDIA_PRIORIDADE = ['malha viária', 'malha viaria', 'rede viária', 'logradouros', 'arruamento']
TERMOS_BAIXA_PRIORIDADE = ['SIG', 'GIS', 'geoprocessamento', 'dados abertos', 'geoportal', 'mapa']

def carregar_dados():
    """Carrega os dados do JSON"""
    with open(PROGRESSO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def classificar_municipio(resultado):
    """Classifica um município por relevância"""
    termos = resultado.get('dados_encontrados', [])
    if not termos:
        return None, 0, []
    
    termos_unicos = list(set([t.lower() for t in termos]))
    
    # Verificar prioridade
    alta = [t for t in termos_unicos if any(p in t for p in TERMOS_ALTA_PRIORIDADE)]
    media = [t for t in termos_unicos if any(p in t for p in TERMOS_MEDIA_PRIORIDADE)]
    baixa = [t for t in termos_unicos if any(p in t for p in TERMOS_BAIXA_PRIORIDADE)]
    
    if alta:
        return 'ALTA', len(alta) * 100 + len(media) * 10 + len(baixa), termos_unicos
    elif media:
        return 'MÉDIA', len(media) * 10 + len(baixa), termos_unicos
    elif baixa:
        return 'BAIXA', len(baixa), termos_unicos
    
    return 'BAIXA', 1, termos_unicos

def gerar_html(dados):
    """Gera o relatório HTML útil"""
    
    resultados = dados.get('resultados', [])
    
    # Classificar municípios
    municipios_relevantes = []
    for r in resultados:
        prioridade, score, termos = classificar_municipio(r)
        if prioridade:
            # Extrair URLs que funcionaram
            urls_sucesso = []
            for busca in r.get('buscas', []):
                if busca.get('status') == 'sucesso' and busca.get('conteudo_encontrado'):
                    urls_sucesso.append({
                        'url': busca.get('url'),
                        'tipo': busca.get('tipo'),
                        'termos': busca.get('termos_encontrados', [])
                    })
            
            municipios_relevantes.append({
                'nome': r['nome'],
                'prioridade': prioridade,
                'score': score,
                'termos': termos,
                'urls': urls_sucesso
            })
    
    # Ordenar por score (mais relevantes primeiro)
    municipios_relevantes.sort(key=lambda x: x['score'], reverse=True)
    
    # Separar por prioridade
    alta = [m for m in municipios_relevantes if m['prioridade'] == 'ALTA']
    media = [m for m in municipios_relevantes if m['prioridade'] == 'MÉDIA']
    baixa = [m for m in municipios_relevantes if m['prioridade'] == 'BAIXA']
    
    # Contar termos totais
    todos_termos = []
    for m in municipios_relevantes:
        todos_termos.extend(m['termos'])
    contagem_termos = Counter(todos_termos)
    
    # Gerar HTML
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Malha Viária SP - Resultados Úteis</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #1a1a2e; 
            color: #eee;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        header {{
            background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; color: #00d9ff; }}
        .subtitle {{ color: #aaa; font-size: 1.1em; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #16213e;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }}
        .stat-card.alta {{ border-left: 5px solid #00ff88; }}
        .stat-card.media {{ border-left: 5px solid #ffaa00; }}
        .stat-card.baixa {{ border-left: 5px solid #888; }}
        .stat-number {{ font-size: 3em; font-weight: bold; }}
        .stat-number.alta {{ color: #00ff88; }}
        .stat-number.media {{ color: #ffaa00; }}
        .stat-number.baixa {{ color: #888; }}
        .stat-label {{ color: #aaa; margin-top: 5px; }}
        
        .section {{
            background: #16213e;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }}
        .section h2 {{
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #333;
        }}
        .section h2.alta {{ color: #00ff88; }}
        .section h2.media {{ color: #ffaa00; }}
        .section h2.baixa {{ color: #888; }}
        
        .municipio-card {{
            background: #0f3460;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        .municipio-card.alta {{ border-left: 4px solid #00ff88; }}
        .municipio-card.media {{ border-left: 4px solid #ffaa00; }}
        .municipio-card.baixa {{ border-left: 4px solid #666; }}
        
        .municipio-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .municipio-nome {{
            font-size: 1.3em;
            font-weight: bold;
            color: #fff;
        }}
        .municipio-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .municipio-badge.alta {{ background: #00ff88; color: #000; }}
        .municipio-badge.media {{ background: #ffaa00; color: #000; }}
        .municipio-badge.baixa {{ background: #666; color: #fff; }}
        
        .termos {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }}
        .termo {{
            background: #1a1a2e;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
        }}
        .termo.destaque {{
            background: #00ff88;
            color: #000;
            font-weight: bold;
        }}
        
        .urls {{
            background: #1a1a2e;
            border-radius: 8px;
            padding: 15px;
        }}
        .url-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }}
        .url-item:last-child {{ margin-bottom: 0; }}
        .url-tipo {{
            background: #0f3460;
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.75em;
            min-width: 100px;
            text-align: center;
        }}
        .url-link {{
            color: #00d9ff;
            text-decoration: none;
            word-break: break-all;
        }}
        .url-link:hover {{ text-decoration: underline; }}
        
        .termos-globais {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .termo-global {{
            background: #0f3460;
            padding: 8px 15px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .termo-count {{
            background: #00d9ff;
            color: #000;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .empty-msg {{
            text-align: center;
            color: #666;
            padding: 40px;
            font-style: italic;
        }}
        
        .action-box {{
            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
            border: 2px solid #00d9ff;
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
        }}
        .action-box h3 {{
            color: #00d9ff;
            margin-bottom: 15px;
        }}
        .action-box ul {{
            list-style: none;
            padding-left: 0;
        }}
        .action-box li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }}
        .action-box li::before {{
            content: "→";
            position: absolute;
            left: 0;
            color: #00ff88;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🗺️ Malha Viária Municipal SP</h1>
            <p class="subtitle">Resultados da Pesquisa em 645 Municípios | {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card alta">
                <div class="stat-number alta">{len(alta)}</div>
                <div class="stat-label">🎯 ALTA PRIORIDADE<br><small>Termos específicos (shapefile, geojson...)</small></div>
            </div>
            <div class="stat-card media">
                <div class="stat-number media">{len(media)}</div>
                <div class="stat-label">⚡ MÉDIA PRIORIDADE<br><small>Termos temáticos (malha viária...)</small></div>
            </div>
            <div class="stat-card baixa">
                <div class="stat-number baixa">{len(baixa)}</div>
                <div class="stat-label">📍 BAIXA PRIORIDADE<br><small>Termos genéricos (SIG, GIS...)</small></div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #00d9ff;">{len(municipios_relevantes)}</div>
                <div class="stat-label">📊 TOTAL COM DADOS<br><small>de 645 municípios</small></div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Termos Mais Encontrados</h2>
            <div class="termos-globais">
'''
    
    for termo, count in contagem_termos.most_common(20):
        html += f'''
                <div class="termo-global">
                    <span>{termo}</span>
                    <span class="termo-count">{count}</span>
                </div>'''
    
    html += '''
            </div>
        </div>
'''
    
    # Seção ALTA PRIORIDADE
    html += '''
        <div class="section">
            <h2 class="alta">🎯 ALTA PRIORIDADE - Dados Vetoriais Potenciais</h2>
'''
    if alta:
        for m in alta[:30]:  # Top 30
            html += gerar_card_municipio(m)
    else:
        html += '<p class="empty-msg">Nenhum município encontrado com termos de alta prioridade (shapefile, geojson, etc.)</p>'
    
    html += '</div>'
    
    # Seção MÉDIA PRIORIDADE
    html += '''
        <div class="section">
            <h2 class="media">⚡ MÉDIA PRIORIDADE - Referências a Malha Viária</h2>
'''
    if media:
        for m in media[:20]:  # Top 20
            html += gerar_card_municipio(m)
    else:
        html += '<p class="empty-msg">Nenhum município encontrado com termos de média prioridade</p>'
    
    html += '</div>'
    
    # Seção BAIXA PRIORIDADE (resumida)
    html += f'''
        <div class="section">
            <h2 class="baixa">📍 BAIXA PRIORIDADE - Menções Genéricas ({len(baixa)} municípios)</h2>
            <p style="color: #888; margin-bottom: 15px;">Municípios que mencionam SIG/GIS mas sem referência específica a dados viários.</p>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
'''
    for m in baixa:
        html += f'<span class="termo">{m["nome"]}</span>'
    
    html += '''
            </div>
        </div>
'''
    
    # Box de ações
    html += '''
        <div class="action-box">
            <h3>📋 Próximos Passos Recomendados</h3>
            <ul>
                <li><strong>ALTA PRIORIDADE:</strong> Acessar os sites listados e procurar links de download direto</li>
                <li>Verificar portais de dados abertos estaduais (SP) e federais (dados.gov.br)</li>
                <li>Contatar secretarias de obras/planejamento dos municípios prioritários</li>
                <li>Buscar em repositórios acadêmicos (USP, UNICAMP, UNESP)</li>
                <li>OpenStreetMap continua sendo a fonte mais completa para malha viária</li>
            </ul>
        </div>
        
        <footer>
            <p>Pesquisa realizada em 645 municípios oficiais do IBGE | São Paulo</p>
        </footer>
    </div>
</body>
</html>
'''
    return html

def gerar_card_municipio(m):
    """Gera o HTML de um card de município"""
    prioridade = m['prioridade'].lower()
    
    html = f'''
            <div class="municipio-card {prioridade}">
                <div class="municipio-header">
                    <span class="municipio-nome">{m['nome']}</span>
                    <span class="municipio-badge {prioridade}">{m['prioridade']}</span>
                </div>
                <div class="termos">
'''
    for termo in m['termos']:
        destaque = 'destaque' if any(p in termo for p in TERMOS_ALTA_PRIORIDADE) else ''
        html += f'<span class="termo {destaque}">{termo}</span>'
    
    html += '''
                </div>
'''
    
    if m['urls']:
        html += '''
                <div class="urls">
'''
        for url_info in m['urls']:
            html += f'''
                    <div class="url-item">
                        <span class="url-tipo">{url_info['tipo']}</span>
                        <a href="{url_info['url']}" target="_blank" class="url-link">{url_info['url']}</a>
                    </div>'''
        html += '''
                </div>
'''
    
    html += '''
            </div>
'''
    return html

def main():
    print("=" * 60)
    print("GERANDO RELATÓRIO ÚTIL")
    print("=" * 60)
    
    # Carregar dados
    print("\n📂 Carregando dados...")
    dados = carregar_dados()
    print(f"   → {dados['municipios_processados']} municípios processados")
    print(f"   → {dados['dados_encontrados']} com algum dado encontrado")
    
    # Gerar HTML
    print("\n📝 Gerando relatório HTML...")
    html = gerar_html(dados)
    
    # Salvar
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "diagnostico_ATUAL.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Relatório salvo em: {output_file}")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
