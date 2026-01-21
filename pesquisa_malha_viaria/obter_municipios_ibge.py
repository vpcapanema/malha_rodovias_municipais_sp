#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtém lista oficial dos 645 municípios de São Paulo via API do IBGE
"""
import requests
import json

def main():
    print("Buscando municípios de SP na API do IBGE...")
    url = 'https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios'
    
    response = requests.get(url)
    municipios = response.json()
    
    print(f"✅ Total: {len(municipios)} municípios")
    
    # Salvar JSON completo
    with open('municipios_sp_ibge_oficial.json', 'w', encoding='utf-8') as f:
        json.dump(municipios, f, ensure_ascii=False, indent=2)
    print("✅ Salvo: municipios_sp_ibge_oficial.json")
    
    # Criar lista Python
    nomes = [m['nome'] for m in municipios]
    with open('LISTA_645_MUNICIPIOS_SP.py', 'w', encoding='utf-8') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""\n')
        f.write('Lista oficial dos 645 municípios de São Paulo\n')
        f.write('Fonte: IBGE - API de Localidades\n')
        f.write('https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios\n')
        f.write('"""\n\n')
        f.write('MUNICIPIOS_SP_645 = [\n')
        for i, nome in enumerate(nomes):
            virgula = ',' if i < len(nomes)-1 else ''
            f.write(f'    "{nome}"{virgula}\n')
        f.write(']\n\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    print(f"Total: {len(MUNICIPIOS_SP_645)} municípios")\n')
    
    print("✅ Salvo: LISTA_645_MUNICIPIOS_SP.py")
    
    # Mostrar amostra
    print("\nPrimeiros 10:")
    for i, n in enumerate(nomes[:10], 1):
        print(f"  {i:3d}. {n}")
    print("...")
    print("\nÚltimos 10:")
    for i, n in enumerate(nomes[-10:], len(nomes)-9):
        print(f"  {i:3d}. {n}")

if __name__ == "__main__":
    main()
