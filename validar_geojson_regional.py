# -*- coding: utf-8 -*-
"""Validação do GeoJSON regional vs JSON."""

import json
from pathlib import Path

reg_json = json.loads(Path('docs/data/regioes_indicadores.json').read_text(encoding='utf-8'))
reg_geo = json.loads(Path('docs/data/regioes_indicadores.geojson').read_text(encoding='utf-8'))

print('=== VALIDAÇÃO DO GEOJSON ===')
print(f'Features no GeoJSON: {len(reg_geo["features"])}')
print(f'RAs no JSON: {len(reg_json)}')
print()

# Comparar
reg_json_dict = {r['RA']: r for r in reg_json}
erros = 0

for feature in reg_geo['features']:
    props = feature['properties']
    nome_ra = props['RA']
    
    if nome_ra not in reg_json_dict:
        print(f'❌ {nome_ra} - Não encontrado no JSON!')
        erros += 1
        continue
    
    ref = reg_json_dict[nome_ra]
    
    # Comparar campos principais
    campos = ['num_municipios', 'extensao_km', 'populacao', 'densidade_area_10k', 'densidade_pop_10k']
    diffs = []
    
    for campo in campos:
        val_geo = props.get(campo, 0)
        val_json = ref.get(campo, 0)
        if abs(val_geo - val_json) > 0.01:
            diffs.append(f'{campo}: GEO={val_geo} vs JSON={val_json}')
    
    if diffs:
        print(f'❌ {nome_ra}')
        for d in diffs:
            print(f'   {d}')
        erros += 1
    else:
        ext = props['extensao_km']
        mun = props['num_municipios']
        print(f'✅ {nome_ra}: {ext:.2f} km, {mun} mun')

print()
print('=== RESULTADO ===')
if erros == 0:
    print('✅ GEOJSON CONSISTENTE COM JSON!')
else:
    print(f'❌ {erros} inconsistências encontradas')
