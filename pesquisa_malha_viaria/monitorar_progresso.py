#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONITORAR PROGRESSO DA PESQUISA
Script para visualizar progresso em tempo real
"""

import json
from pathlib import Path
from datetime import datetime

def monitorar_progresso():
    """Monitora e exibe progresso"""
    progresso_file = Path("pesquisa_dados/progresso/progresso.json")
    
    if not progresso_file.exists():
        print("⏳ Pesquisa ainda não iniciou...")
        return
    
    with open(progresso_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    total_munis = stats['total_municipios']
    total_buscas = stats['total_buscas']
    sucesso = stats['sucesso']
    falha = stats['falha']
    dados_encontrados = stats['dados_encontrados']
    resultados = stats['resultados']
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    PROGRESSO DA PESQUISA - 645 MUNICÍPIOS                 ║
║                          {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
╚════════════════════════════════════════════════════════════════════════════╝

📊 ESTATÍSTICAS GERAIS:
   Municípios processados: {total_munis}/645
   Total de buscas realizadas: {total_buscas}
   Acessos bem-sucedidos: {sucesso}
   Falhas: {falha}
   
📈 TAXAS:
   Taxa de sucesso: {(sucesso / max(total_buscas, 1) * 100):.1f}%
   Taxa de falha: {(falha / max(total_buscas, 1) * 100):.1f}%
   Municípios com dados: {sum(1 for r in resultados if r['status'] == 'acessado')} 
   Taxa de municípios com dados: {(sum(1 for r in resultados if r['status'] == 'acessado') / max(total_munis, 1) * 100):.1f}%

🎯 ÚLTIMOS 10 RESULTADOS:
""")
    
    for r in resultados[-10:]:
        status_icon = "✓" if r['status'] == 'acessado' else "✗"
        buscas_ok = sum(1 for b in r['buscas'] if b['status'] == 'sucesso')
        print(f"   {status_icon} [{r['id']:3d}] {r['nome']:30s} - {buscas_ok} buscas OK")
    
    print(f"""
💾 ARQUIVO DE PROGRESSO: pesquisa_dados/progresso/progresso.json
📄 RELATÓRIO: pesquisa_dados/relatorios/

⏳ Pesquisa em andamento... {total_munis/645*100:.1f}% completo
""")

if __name__ == "__main__":
    monitorar_progresso()
