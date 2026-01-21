import geopandas as gpd

# Ver colunas dos municípios
mun = gpd.read_file("dados/malha_municipal_sp.gpkg")
print("Colunas dos municípios:", mun.columns.tolist())
print(f"Total de registros: {len(mun)}")
print("\nPrimeiras linhas:")
print(mun.head())
