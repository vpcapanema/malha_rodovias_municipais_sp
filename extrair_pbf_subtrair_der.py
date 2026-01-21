"""
Extração de vetores OSM do arquivo PBF para São Paulo
Usando biblioteca osmium

Autor: Análise automatizada
Data: Janeiro/2026
"""

import osmium
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configurações
PBF_FILE = r'D:\ESTUDO_VICINAIS_V2\dados\Base_OSM\sudeste-251111.osm.pbf'
LIMITE_SP = r'D:\ESTUDO_VICINAIS_V2\dados\au_ibge.gpkg'  # Para pegar bounds de SP
OUTPUT_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\dados_processados')
INTERMEDIARIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\intermediarios')
RELATORIO_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\resultados\relatorios')

# Bounds aproximados do Estado de São Paulo
# minx, miny, maxx, maxy
SP_BOUNDS = (-53.1, -25.3, -44.1, -19.8)


class HighwayHandler(osmium.SimpleHandler):
    """Handler para extrair vias (highways) do arquivo PBF"""
    
    def __init__(self):
        super().__init__()
        self.ways = []
        self.count = 0
        self.sp_count = 0
        
    def way(self, w):
        """Processa cada way do arquivo"""
        self.count += 1
        
        if self.count % 500000 == 0:
            print(f"  Processadas {self.count:,} ways, {self.sp_count:,} em SP...")
        
        # Verificar se é uma highway
        if 'highway' not in w.tags:
            return
            
        # Extrair coordenadas
        try:
            coords = [(n.lon, n.lat) for n in w.nodes]
            
            # Verificar se pelo menos um ponto está dentro de SP
            in_sp = False
            for lon, lat in coords:
                if (SP_BOUNDS[0] <= lon <= SP_BOUNDS[2] and 
                    SP_BOUNDS[1] <= lat <= SP_BOUNDS[3]):
                    in_sp = True
                    break
            
            if not in_sp:
                return
                
            if len(coords) < 2:
                return
                
            self.sp_count += 1
            
            # Extrair atributos
            way_data = {
                'osm_id': w.id,
                'name': w.tags.get('name', ''),
                'highway': w.tags.get('highway', ''),
                'ref': w.tags.get('ref', ''),
                'surface': w.tags.get('surface', ''),
                'lanes': w.tags.get('lanes', ''),
                'maxspeed': w.tags.get('maxspeed', ''),
                'oneway': w.tags.get('oneway', ''),
                'coords': coords
            }
            
            self.ways.append(way_data)
            
        except Exception as e:
            pass  # Ignorar ways com problemas de geometria


def extrair_highways_pbf():
    """Extrai highways do arquivo PBF"""
    print("="*60)
    print("EXTRAÇÃO DE HIGHWAYS DO ARQUIVO PBF")
    print("="*60)
    
    print(f"\nArquivo PBF: {PBF_FILE}")
    print(f"Bounds SP: {SP_BOUNDS}")
    
    # Criar handler
    print("\nProcessando arquivo PBF (pode demorar vários minutos)...")
    handler = HighwayHandler()
    
    # Processar arquivo
    handler.apply_file(PBF_FILE, locations=True)
    
    print(f"\nTotal de ways processadas: {handler.count:,}")
    print(f"Highways em SP: {handler.sp_count:,}")
    
    # Converter para GeoDataFrame
    print("\nConvertendo para GeoDataFrame...")
    
    geometries = []
    data = []
    
    for way in handler.ways:
        try:
            coords = way.pop('coords')
            if len(coords) >= 2:
                geom = LineString(coords)
                geometries.append(geom)
                data.append(way)
        except:
            continue
    
    gdf = gpd.GeoDataFrame(data, geometry=geometries, crs='EPSG:4326')
    
    print(f"GeoDataFrame criado: {len(gdf):,} features")
    
    return gdf


def salvar_base_osm(gdf):
    """Salva a base OSM extraída"""
    output_file = INTERMEDIARIO_DIR / 'osm_sp_highways.gpkg'
    print(f"\nSalvando: {output_file}")
    gdf.to_file(output_file, driver='GPKG')
    return output_file


def subtrair_der(osm_gdf):
    """Subtrai a malha do DER da base OSM"""
    print("\n" + "="*60)
    print("SUBTRAÇÃO DA MALHA DER")
    print("="*60)
    
    MALHA_DER = r'D:\ESTUDO_VICINAIS_V2\dados\Sistema Rodoviário Estadual\MALHA_RODOVIARIA\MALHA_OUT.shp'
    BUFFER_SUBTRACAO = 15  # metros
    
    print(f"\nCarregando malha DER: {MALHA_DER}")
    der = gpd.read_file(MALHA_DER)
    print(f"  Total DER: {len(der):,}")
    
    # Reprojetar para metros
    print("\nReprojetando para sistema métrico...")
    osm_utm = osm_gdf.to_crs(epsg=31983)
    der_utm = der.to_crs(epsg=31983)
    
    # Filtrar estaduais e federais
    der_ef = der_utm[der_utm['Jurisdicao'].isin(['Estadual', 'Federal'])]
    print(f"  DER estadual/federal: {len(der_ef):,}")
    
    # Buffer
    print(f"\nCriando buffer de {BUFFER_SUBTRACAO}m...")
    der_buffer = unary_union(der_ef.geometry.buffer(BUFFER_SUBTRACAO))
    
    # Calcular sobreposição
    print("Calculando sobreposições...")
    osm_utm = osm_utm.reset_index(drop=True)
    
    prop_sobreposta = []
    total = len(osm_utm)
    
    for idx, row in osm_utm.iterrows():
        if idx % 100000 == 0:
            print(f"  {idx:,}/{total:,} ({100*idx/total:.1f}%)...")
        
        try:
            if row.geometry.intersects(der_buffer):
                intersecao = row.geometry.intersection(der_buffer)
                if not intersecao.is_empty and row.geometry.length > 0:
                    prop = intersecao.length / row.geometry.length
                else:
                    prop = 0
            else:
                prop = 0
        except:
            prop = 0
        
        prop_sobreposta.append(prop)
    
    osm_utm['prop_sobreposta'] = prop_sobreposta
    
    # Remover >50% sobrepostos
    mascara = osm_utm['prop_sobreposta'] < 0.5
    removidos = (~mascara).sum()
    
    print(f"\n  Removidos (>50% sobreposição): {removidos:,}")
    
    osm_filtrado = osm_utm[mascara].copy()
    osm_filtrado = osm_filtrado.drop(columns=['prop_sobreposta'])
    osm_filtrado['comprimento_m'] = osm_filtrado.geometry.length
    osm_filtrado = osm_filtrado.to_crs(epsg=4326)
    
    return osm_filtrado, removidos


def main():
    print("="*60)
    print("EXTRAÇÃO OSM PBF E SUBTRAÇÃO DER")
    print("="*60)
    print(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Extrair highways do PBF
    osm_gdf = extrair_highways_pbf()
    
    # 2. Salvar base intermediária
    osm_file = salvar_base_osm(osm_gdf)
    
    # 3. Estatísticas
    print("\n" + "="*60)
    print("ESTATÍSTICAS DA BASE EXTRAÍDA")
    print("="*60)
    print(f"\nDistribuição por highway:")
    print(osm_gdf['highway'].value_counts().head(15).to_string())
    
    # 4. Subtrair DER
    osm_menos_der, removidos = subtrair_der(osm_gdf)
    
    # 5. Salvar resultado final
    output_file = OUTPUT_DIR / 'osm_sp_menos_der.gpkg'
    print(f"\nSalvando resultado final: {output_file}")
    osm_menos_der.to_file(output_file, driver='GPKG')
    
    # Relatório
    relatorio_file = RELATORIO_DIR / 'relatorio_extracao_pbf.txt'
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE EXTRAÇÃO PBF E SUBTRAÇÃO DER\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Arquivo PBF: {PBF_FILE}\n\n")
        f.write(f"Highways extraídas: {len(osm_gdf):,}\n")
        f.write(f"Removidas (DER): {removidos:,}\n")
        f.write(f"Resultado final: {len(osm_menos_der):,}\n\n")
        f.write(f"Extensão total: {osm_menos_der['comprimento_m'].sum()/1000:,.1f} km\n\n")
        f.write("Distribuição por highway:\n")
        f.write(osm_menos_der['highway'].value_counts().to_string())
    
    print(f"\nRelatório: {relatorio_file}")
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    print(f"Base extraída: {len(osm_gdf):,} highways")
    print(f"Removidas (DER): {removidos:,}")
    print(f"Resultado final: {len(osm_menos_der):,}")
    print(f"Extensão: {osm_menos_der['comprimento_m'].sum()/1000:,.1f} km")
    print(f"\nArquivo: {output_file}")
    print("\n✅ Processamento concluído!")
    
    return osm_menos_der


if __name__ == "__main__":
    resultado = main()
