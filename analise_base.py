import geopandas as gpd
import pandas as pd

# Carregar a base de linhas
print("Carregando dados...")
gdf = gpd.read_file(r'D:\ESTUDO_VICINAIS_V2\dados\base_linhas.gpkg')

print(f"\n=== RESUMO GERAL ===")
print(f"Total de registros: {len(gdf):,}")
print(f"CRS: {gdf.crs}")

print("\n=== ANÁLISE POR TIPO DE HIGHWAY ===")
for hw in ['residential', 'unclassified', 'service', 'tertiary', 'secondary', 'primary', 'motorway', 'trunk', 'living_street']:
    subset = gdf[gdf['highway'] == hw]
    com_ref = subset['ref'].notna().sum()
    com_nome = subset['name'].notna().sum()
    print(f"\n--- {hw} ({len(subset):,} registros) ---")
    print(f"  Com referência (ref): {com_ref:,} ({100*com_ref/len(subset):.1f}%)")
    print(f"  Com nome: {com_nome:,} ({100*com_nome/len(subset):.1f}%)")
    if com_nome > 0:
        print(f"  Exemplos de nomes: {subset[subset['name'].notna()]['name'].head(3).tolist()}")
    if com_ref > 0:
        print(f"  Exemplos de refs: {subset[subset['ref'].notna()]['ref'].head(3).tolist()}")

# Análise de padrões de nomes para identificar vias urbanas
print("\n=== PADRÕES DE NOMES (para identificar vias urbanas) ===")
nomes = gdf[gdf['name'].notna()]['name']
print(f"Total com nome: {len(nomes):,}")

# Contagem de padrões de início de nomes
padrao_inicio = nomes.str.extract(r'^(\w+)', expand=False).value_counts().head(30)
print("\nPadrões mais comuns no início dos nomes:")
print(padrao_inicio.to_string())

# Identificar vias que parecem urbanas
padroes_urbanos = ['Rua', 'Avenida', 'Av.', 'Travessa', 'Alameda', 'Praça', 'Largo', 'Beco', 'Viela', 'Estrada']
for padrao in padroes_urbanos:
    count = nomes.str.startswith(padrao, na=False).sum()
    print(f"  Começam com '{padrao}': {count:,}")

# Identificar estradas vicinais e rurais
print("\n=== PADRÕES DE ESTRADAS VICINAIS/RURAIS ===")
padroes_vicinais = ['Estrada', 'Vicinal', 'SPA', 'SPI', 'SPM', 'Municipal', 'Rodovia', 'Acesso']
for padrao in padroes_vicinais:
    count = nomes.str.contains(padrao, na=False, case=False).sum()
    print(f"  Contém '{padrao}': {count:,}")

# Análise cruzada: highway + ref
print("\n=== CRUZAMENTO HIGHWAY x REFERÊNCIA ===")
for hw in ['unclassified', 'tertiary', 'secondary', 'primary']:
    subset = gdf[gdf['highway'] == hw]
    com_br = subset['ref'].str.contains('BR-', na=False).sum()
    com_sp = subset['ref'].str.contains('SP-', na=False).sum()
    sem_ref = subset['ref'].isna().sum()
    print(f"{hw}: BR={com_br:,}, SP={com_sp:,}, sem_ref={sem_ref:,}")

print("\n=== ANÁLISE MOTORWAY/TRUNK (rodovias principais) ===")
for hw in ['motorway', 'motorway_link', 'trunk', 'trunk_link']:
    subset = gdf[gdf['highway'] == hw]
    print(f"\n{hw}: {len(subset):,} registros")
    if len(subset) > 0:
        refs = subset[subset['ref'].notna()]['ref'].value_counts().head(5)
        print(f"  Top refs: {refs.to_dict()}")
