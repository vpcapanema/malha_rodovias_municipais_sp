"""
Verificar se o GeoJSON atual preservou a coluna metros
"""
import geopandas as gpd

print("=" * 70)
print("VERIFICANDO GEOJSON ATUAL")
print("=" * 70)

gdf = gpd.read_file('docs/data/malha_vicinais.geojson')

print(f"\n[INFO] Segmentos: {len(gdf)}")
print(f"[INFO] CRS: {gdf.crs}")

print("\n[COLUNAS]")
print(gdf.columns.tolist())

print("\n[VERIFICANDO COLUNA METROS]")
if 'metros' in gdf.columns:
    total_metros = gdf['metros'].sum()
    print(f"✅ Coluna metros EXISTE!")
    print(f"   Total: {total_metros:,.2f} metros")
    print(f"   Total: {total_metros/1000:,.2f} km")
else:
    print("❌ Coluna metros NÃO EXISTE!")

print("\n[CALCULANDO GEOMETRY.LENGTH]")
gdf_utm = gdf.to_crs(epsg=31983)
comprimento_calc = gdf_utm.geometry.length.sum()
print(f"   Total calculado: {comprimento_calc:,.2f} metros")
print(f"   Total calculado: {comprimento_calc/1000:,.2f} km")

print("\n[COMPARAÇÃO]")
print(f"   Valor esperado (Silvio): 25.918,58 km")
if 'metros' in gdf.columns:
    print(f"   Valor no GeoJSON (metros): {gdf['metros'].sum()/1000:,.2f} km")
    print(f"   Diferença: {abs(25918.58 - gdf['metros'].sum()/1000):,.2f} km")
