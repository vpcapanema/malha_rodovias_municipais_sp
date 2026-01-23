# -*- coding: utf-8 -*-
"""
Gera GeoJSON das Regiões Administrativas com todas as métricas/indicadores.

Combina:
- regioes_administrativas_sp.geojson (geometrias por município, agregadas por RA)
- regioes_indicadores.json (indicadores calculados por RA)

Saída:
- regioes_indicadores.geojson (uma feature por RA com geometria e indicadores)
"""

import json
from pathlib import Path
from collections import defaultdict

# Caminhos
DOCS_DATA = Path("docs/data")
GEOJSON_BASE = DOCS_DATA / "regioes_administrativas_sp.geojson"
INDICADORES = DOCS_DATA / "regioes_indicadores_total.json"  # Usar arquivo com ambas as malhas
SAIDA = DOCS_DATA / "regioes_indicadores.geojson"


def carregar_json(caminho: Path) -> dict | list:
    """Carrega arquivo JSON com encoding UTF-8."""
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_geojson(dados: dict, caminho: Path):
    """Salva GeoJSON com encoding UTF-8 e formatação."""
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"✓ Salvo: {caminho}")
    print(f"  Tamanho: {caminho.stat().st_size / 1024 / 1024:.2f} MB")


def normalizar_nome_ra(nome: str) -> str:
    """Normaliza nome de RA corrigindo problemas de encoding."""
    # Mapa de correções de encoding UTF-8 malformado
    correcoes = {
        "Ã£": "ã",
        "Ã©": "é",
        "Ã­": "í",
        "Ã§": "ç",
        "Ã³": "ó",
        "Ã¡": "á",
        "Ãª": "ê",
        "Ã": "Á",  # Para casos especiais
    }
    resultado = nome
    for errado, correto in correcoes.items():
        resultado = resultado.replace(errado, correto)
    return resultado


def agregar_geometrias_por_ra(geojson: dict) -> dict:
    """
    Agrega geometrias de municípios por RA.
    
    O GeoJSON base tem uma feature por município. Precisamos agregar
    todas as geometrias de cada RA em um único MultiPolygon.
    """
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union
    
    # Agrupar features por RA (com normalização de nomes)
    features_por_ra = defaultdict(list)
    for feature in geojson["features"]:
        ra = feature["properties"].get("RA", "")
        if ra:
            ra_normalizada = normalizar_nome_ra(ra)
            features_por_ra[ra_normalizada].append(feature)
    
    print(f"\n📊 RAs encontradas no GeoJSON: {len(features_por_ra)}")
    for ra, features in sorted(features_por_ra.items()):
        print(f"   {ra}: {len(features)} municípios")
    
    # Agregar geometrias
    geometrias_agregadas = {}
    for ra, features in features_por_ra.items():
        geometrias = [shape(f["geometry"]) for f in features]
        uniao = unary_union(geometrias)
        geometrias_agregadas[ra] = mapping(uniao)
    
    return geometrias_agregadas


def criar_geojson_regioes(geometrias: dict, indicadores: list) -> dict:
    """Cria GeoJSON final combinando geometrias e indicadores (OSM + Total)."""
    
    # Indexar indicadores por RA
    indicadores_por_ra = {ind["RA"]: ind for ind in indicadores}
    
    print(f"\n📋 Indicadores carregados: {len(indicadores_por_ra)} RAs")
    
    features = []
    for ra_nome, geometria in geometrias.items():
        # Buscar indicadores da RA
        ind = indicadores_por_ra.get(ra_nome, {})
        
        # Criar propriedades com AMBAS as malhas (OSM e Total)
        properties = {
            "RA": ra_nome,
            "num_municipios": ind.get("num_municipios", 0),
            "area_km2": ind.get("area_km2", 0),
            "populacao": ind.get("populacao", 0),
            # Malha OSM
            "extensao_km": ind.get("extensao_osm_km", 0),  # Compatibilidade
            "extensao_osm_km": ind.get("extensao_osm_km", 0),
            "densidade_area_10k": ind.get("densidade_osm_area_10k", 0),
            "densidade_pop_10k": ind.get("densidade_osm_pop_10k", 0),
            # Malha Total (OSM + DER)
            "extensao_total_km": ind.get("extensao_total_km", 0),
            "densidade_total_area_10k": ind.get("densidade_total_area_10k", 0),
            "densidade_total_area_abs": ind.get("densidade_total_area_abs", 0),
            "densidade_total_pop_10k": ind.get("densidade_total_pop_10k", 0),
            "extensao_total_media_mun": ind.get("extensao_total_media_mun", 0),
            # Desvios (baseados na malha total)
            "desvio_dens_area": ind.get("desvio_total_dens_area", 0),
            "desvio_dens_pop": ind.get("desvio_total_dens_pop", 0),
            # Extensão média por município (OSM)
            "extensao_media_mun": round(ind.get("extensao_osm_km", 0) / max(ind.get("num_municipios", 1), 1), 2),
        }
        
        feature = {
            "type": "Feature",
            "properties": properties,
            "geometry": geometria
        }
        features.append(feature)
        
        if ind:
            print(f"   ✓ {ra_nome}: OSM={ind.get('extensao_osm_km', 0):.2f} km | Total={ind.get('extensao_total_km', 0):.2f} km")
        else:
            print(f"   ⚠ {ra_nome}: sem indicadores")
    
    return {
        "type": "FeatureCollection",
        "features": features
    }
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


def main():
    print("=" * 60)
    print("GERADOR DE GEOJSON DAS REGIÕES ADMINISTRATIVAS")
    print("=" * 60)
    
    # Verificar arquivos de entrada
    if not GEOJSON_BASE.exists():
        print(f"❌ Arquivo não encontrado: {GEOJSON_BASE}")
        return
    
    if not INDICADORES.exists():
        print(f"❌ Arquivo não encontrado: {INDICADORES}")
        return
    
    # Carregar dados
    print(f"\n📂 Carregando GeoJSON base: {GEOJSON_BASE}")
    geojson_base = carregar_json(GEOJSON_BASE)
    print(f"   Features: {len(geojson_base['features'])}")
    
    print(f"\n📂 Carregando indicadores: {INDICADORES}")
    indicadores = carregar_json(INDICADORES)
    print(f"   RAs: {len(indicadores)}")
    
    # Agregar geometrias por RA
    print("\n🔄 Agregando geometrias por RA...")
    geometrias = agregar_geometrias_por_ra(geojson_base)
    
    # Criar GeoJSON final
    print("\n🔄 Criando GeoJSON com indicadores...")
    geojson_final = criar_geojson_regioes(geometrias, indicadores)
    
    # Salvar
    print(f"\n💾 Salvando GeoJSON final...")
    salvar_geojson(geojson_final, SAIDA)
    
    # Resumo
    print("\n" + "=" * 60)
    print("✅ GEOJSON GERADO COM SUCESSO!")
    print("=" * 60)
    print(f"\n📄 Arquivo: {SAIDA}")
    print(f"   Features: {len(geojson_final['features'])} RAs")
    
    # Estatísticas
    total_extensao_osm = sum(f["properties"]["extensao_osm_km"] for f in geojson_final["features"])
    total_extensao_total = sum(f["properties"]["extensao_total_km"] for f in geojson_final["features"])
    total_populacao = sum(f["properties"]["populacao"] for f in geojson_final["features"])
    total_municipios = sum(f["properties"]["num_municipios"] for f in geojson_final["features"])
    
    print(f"\n📊 TOTAIS:")
    print(f"   Extensão OSM: {total_extensao_osm:,.2f} km")
    print(f"   Extensão Total (OSM + DER): {total_extensao_total:,.2f} km")
    print(f"   População: {total_populacao:,}")
    print(f"   Municípios: {total_municipios}")


if __name__ == "__main__":
    main()
