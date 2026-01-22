"""
Validar valores finais em todos os JSONs
"""
import json

print("=" * 70)
print("VALIDAÇÃO FINAL DOS TOTAIS")
print("=" * 70)

# Carregar arquivos
with open('docs/data/segmentos_estatisticas.json', encoding='utf-8') as f:
    seg = json.load(f)

with open('docs/data/municipios_indicadores.json', encoding='utf-8') as f:
    mun = json.load(f)

with open('docs/data/estatisticas_completas.json', encoding='utf-8') as f:
    est = json.load(f)

# Extrair totais
total_seg = seg['estatisticas_segmentos']['extensao_total_km']
total_mun = sum(m['extensao_km'] for m in mun)
total_geral = est['geral']['extensao_total_km']
total_municipal = est['municipal']['extensao']['total']

print("\n[TOTAIS ENCONTRADOS]")
print(f"  segmentos_estatisticas.json:    {total_seg:,.2f} km")
print(f"  municipios_indicadores.json:    {total_mun:,.2f} km")
print(f"  estatisticas_completas (geral): {total_geral:,.2f} km")
print(f"  estatisticas_completas (munic): {total_municipal:,.2f} km")

print("\n[VALOR ESPERADO]")
print(f"  Malha Silvio (coluna metros):   25.918,58 km")

print("\n[VALIDAÇÃO]")
valores = [total_seg, total_mun, total_geral, total_municipal]
valor_esperado = 25918.58

todos_corretos = all(abs(v - valor_esperado) < 0.01 for v in valores)

if todos_corretos:
    print("  ✅ TODOS OS VALORES CONFEREM!")
    print("  ✅ Total exato: 25.918,58 km em todos os arquivos")
else:
    print("  ❌ DIFERENÇAS ENCONTRADAS:")
    for i, (nome, valor) in enumerate([
        ('segmentos', total_seg),
        ('municipios', total_mun),
        ('geral', total_geral),
        ('municipal', total_municipal)
    ]):
        diff = valor - valor_esperado
        if abs(diff) >= 0.01:
            print(f"     {nome}: diferença de {diff:+.2f} km")

print("\n" + "=" * 70)
