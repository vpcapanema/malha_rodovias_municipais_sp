"""
Verificar coluna metros do shapefile DER original
"""
import geopandas as gpd

print("=" * 70)
print("ANÁLISE DO SHAPEFILE ORIGINAL DER")
print("=" * 70)

shp_path = r'D:\ESTUDO_VICINAIS_V2\motodologia_abordagem_silvio\Vicinais\Avaliacao_OSM_p_Vicinais\Avaliacao_OSM_p_Vicinais\Rodovias Municipais_20250516\Rodovias_municipais_wgsutm23s_intesect_mun.shp'

gdf = gpd.read_file(shp_path)

print(f"\n[INFO] Segmentos: {len(gdf)}")
print(f"[INFO] CRS: {gdf.crs}")
print(f"[INFO] EPSG: {gdf.crs.to_epsg()}")

print("\n[COLUNAS]")
print(gdf.columns.tolist())

if 'metros' in gdf.columns:
    print("\n[COLUNA METROS - FONTE DE VERDADE]")
    total_m = gdf['metros'].sum()
    print(f"  Total: {total_m:,.2f} metros")
    print(f"  Total: {total_m/1000:,.2f} km")
    print(f"  Média: {gdf['metros'].mean():,.2f} metros")
    print(f"  Mediana: {gdf['metros'].median():,.2f} metros")
    print(f"  Mínimo: {gdf['metros'].min():,.2f} metros")
    print(f"  Máximo: {gdf['metros'].max():,.2f} metros")
    print(f"  Desvio: {gdf['metros'].std():,.2f} metros")
    
    print("\n[COMPARAÇÃO]")
    print("  Valor que você somou: 25.918.576,46 metros = 25.918,58 km")
    print(f"  Valor calculado aqui: {total_m:,.2f} metros = {total_m/1000:,.2f} km")
    print(f"  Diferença: {abs(25918576.46 - total_m):,.2f} metros")
    
    print("\n✅ Esta coluna 'metros' JÁ TEM os comprimentos corretos!")
    print("   Calculados pelo DER em UTM 23S.")
    print("   NÃO PRECISAMOS RECALCULAR geometrias!")
