"""
Conversão de arquivo OSM PBF para GeoPackage
Extrai apenas as linhas (ways) com highway para São Paulo

Autor: Análise automatizada
Data: Janeiro/2026
"""

import osmium
import geopandas as gpd
from shapely.geometry import LineString
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configurações
PBF_FILE = r'D:\ESTUDO_VICINAIS_V2\dados\Base_OSM\sudeste-251111.osm.pbf'
OUTPUT_DIR = Path(r'D:\ESTUDO_VICINAIS_V2\dados')

# Bounds aproximados do Estado de São Paulo
SP_BOUNDS = (-53.1, -25.3, -44.1, -19.8)


class HighwayHandler(osmium.SimpleHandler):
    """Handler para extrair highways do arquivo PBF"""
    
    def __init__(self):
        super().__init__()
        self.ways = []
        self.count = 0
        self.highway_count = 0
        self.sp_count = 0
        
    def way(self, w):
        """Processa cada way"""
        self.count += 1
        
        if self.count % 1000000 == 0:
            print(f"  {self.count:,} ways processadas, {self.sp_count:,} highways em SP...")
        
        # Apenas highways
        if 'highway' not in w.tags:
            return
            
        self.highway_count += 1
        
        try:
            coords = [(n.lon, n.lat) for n in w.nodes]
            
            if len(coords) < 2:
                return
            
            # Verificar se está em SP (pelo menos um ponto)
            in_sp = False
            for lon, lat in coords:
                if (SP_BOUNDS[0] <= lon <= SP_BOUNDS[2] and 
                    SP_BOUNDS[1] <= lat <= SP_BOUNDS[3]):
                    in_sp = True
                    break
            
            if not in_sp:
                return
                
            self.sp_count += 1
            
            self.ways.append({
                'osm_id': w.id,
                'name': w.tags.get('name', ''),
                'highway': w.tags.get('highway', ''),
                'ref': w.tags.get('ref', ''),
                'surface': w.tags.get('surface', ''),
                'lanes': w.tags.get('lanes', ''),
                'maxspeed': w.tags.get('maxspeed', ''),
                'oneway': w.tags.get('oneway', ''),
                'coords': coords
            })
            
        except Exception:
            pass


def main():
    print("="*60)
    print("CONVERSÃO PBF -> GEOPACKAGE")
    print("="*60)
    print(f"Início: {datetime.now().strftime('%H:%M:%S')}")
    print(f"\nArquivo: {PBF_FILE}")
    print(f"Bounds SP: {SP_BOUNDS}")
    
    # Processar PBF
    print("\nProcessando arquivo PBF (aguarde, ~800MB)...")
    handler = HighwayHandler()
    handler.apply_file(PBF_FILE, locations=True)
    
    print(f"\nResultado:")
    print(f"  Total ways: {handler.count:,}")
    print(f"  Highways: {handler.highway_count:,}")
    print(f"  Highways em SP: {handler.sp_count:,}")
    
    # Converter para GeoDataFrame
    print("\nCriando GeoDataFrame...")
    
    geometries = []
    data = []
    
    for way in handler.ways:
        coords = way.pop('coords')
        try:
            geom = LineString(coords)
            geometries.append(geom)
            data.append(way)
        except:
            continue
    
    gdf = gpd.GeoDataFrame(data, geometry=geometries, crs='EPSG:4326')
    print(f"  Features: {len(gdf):,}")
    
    # Calcular comprimento
    print("Calculando comprimentos...")
    gdf_utm = gdf.to_crs(epsg=31983)
    gdf['comprimento_m'] = gdf_utm.geometry.length
    
    # Estatísticas
    print(f"\nDistribuição por highway:")
    print(gdf['highway'].value_counts().head(15).to_string())
    
    ext_km = gdf['comprimento_m'].sum() / 1000
    print(f"\nExtensão total: {ext_km:,.1f} km")
    
    # Salvar
    output_file = OUTPUT_DIR / 'osm_sp_linhas.gpkg'
    print(f"\nSalvando: {output_file}")
    gdf.to_file(output_file, driver='GPKG')
    
    print(f"\nFim: {datetime.now().strftime('%H:%M:%S')}")
    print("✅ Conversão concluída!")
    
    return gdf


if __name__ == "__main__":
    resultado = main()
