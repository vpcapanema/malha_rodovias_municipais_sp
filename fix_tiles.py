#!/usr/bin/env python3
import re

# Arquivo municipal
file_path = "docs/js/resultados_municipal.js"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corrigir getDivisoesParaZoom
content = re.sub(
    r'function getDivisoesParaZoom\(zoom\)\s*{\s*return Math\.pow\(2, zoom - 8\);',
    'function getDivisoesParaZoom(zoom) {\n        return Math.pow(2, zoom - 7); // 8->2, 9->4, 10->8, 11->16',
    content
)

# 2. Adicionar loadedCount = 0 na função carregarTilesVisiveis
content = re.sub(
    r'function carregarTilesVisiveis\(\)\s*{\s*if \(isLoading\) return;\s*const novoZoom',
    'function carregarTilesVisiveis() {\n        if (isLoading) return;\n        \n        let loadedCount = 0;\n        const novoZoom',
    content
)

# 3. Corrigir o tratamento de erro do catch
content = re.sub(
    r'\.catch\(err => \{\s*if \(!err\.includes\(',
    '.catch(err => {\n                        const errMsg = err?.message || String(err) || \'\';\n                        if (!errMsg.includes(',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Arquivo {file_path} atualizado com sucesso!")

# Fazer o mesmo para regional
file_path_regional = "docs/js/resultados_regional.js"
with open(file_path_regional, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r'function getDivisoesParaZoom\(zoom\)\s*{\s*return Math\.pow\(2, zoom - 8\);',
    'function getDivisoesParaZoom(zoom) {\n        return Math.pow(2, zoom - 7); // 8->2, 9->4, 10->8, 11->16',
    content
)

content = re.sub(
    r'function carregarTilesVisiveis\(\)\s*{\s*if \(isLoading\) return;\s*const novoZoom',
    'function carregarTilesVisiveis() {\n        if (isLoading) return;\n        \n        let loadedCount = 0;\n        const novoZoom',
    content
)

content = re.sub(
    r'\.catch\(err => \{\s*if \(!err\.includes\(',
    '.catch(err => {\n                        const errMsg = err?.message || String(err) || \'\';\n                        if (!errMsg.includes(',
    content
)

with open(file_path_regional, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Arquivo {file_path_regional} atualizado com sucesso!")
