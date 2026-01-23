"""
Script para corrigir codificação UTF-8 dos arquivos JSON
Converte caracteres mal codificados (Latin-1 interpretado como UTF-8) para UTF-8 correto
"""

import json
from pathlib import Path

def fix_encoding(text):
    """
    Corrige texto com codificação UTF-8 mal interpretada
    Converte de UTF-8 incorreto (Latin-1 → UTF-8) para UTF-8 correto
    """
    try:
        # Se o texto já está em bytes UTF-8 mal interpretados,
        # decode como Latin-1 e então encode/decode corretamente
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Se falhar, retorna o texto original
        return text

def fix_dict(obj):
    """Aplica fix_encoding recursivamente em dicionários e listas"""
    if isinstance(obj, dict):
        return {k: fix_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_dict(item) for item in obj]
    elif isinstance(obj, str):
        return fix_encoding(obj)
    else:
        return obj

# Arquivos a corrigir
arquivos = [
    'docs/data/municipios_indicadores.json',
    'docs/data/municipios_totais.geojson',
]

print("=" * 70)
print("CORRIGINDO CODIFICAÇÃO UTF-8 DOS ARQUIVOS JSON")
print("=" * 70)
print()

for arquivo_path in arquivos:
    arquivo = Path(arquivo_path)
    
    if not arquivo.exists():
        print(f"[AVISO] Arquivo não encontrado: {arquivo}")
        continue
    
    print(f"Processando: {arquivo}")
    
    try:
        # Ler arquivo
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Aplicar correção
        dados_corrigidos = fix_dict(dados)
        
        # Salvar com codificação correta
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_corrigidos, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ Arquivo corrigido e salvo")
        
    except Exception as e:
        print(f"  ✗ ERRO ao processar: {e}")
    
    print()

print("=" * 70)
print("PROCESSO CONCLUÍDO")
print("=" * 70)
