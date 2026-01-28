// Loader global para tiles pré-carregados
let tilesCache = null;
let tilesCachePromise = null;

async function carregarTilesGlobais() {
    if (tilesCache) return tilesCache;
    if (tilesCachePromise) return await tilesCachePromise;
    
    tilesCachePromise = fetch(`${baseUrl}/data/tiles/tiles_z10.json`)
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            tilesCache = data.tiles;
            console.log(`✅ Tiles globais carregados: ${Object.keys(tilesCache).length} tiles`);
            return tilesCache;
        })
        .catch(err => {
            console.warn(`⚠️ Erro ao carregar tiles: ${err}`);
            tilesCachePromise = null;
            throw err;
        });
    
    return await tilesCachePromise;
}

// Substitui o carregamento de tiles individuais
async function obterTile(zoom, x, y) {
    const tiles = await carregarTilesGlobais();
    if (zoom !== 10) {
        console.warn(`⚠️ Zoom ${zoom} não disponível, usando zoom 10`);
        zoom = 10;
    }
    
    const tileKey = `${x}/${y}`;
    if (!tiles[tileKey]) {
        console.warn(`⚠️ Tile ${zoom}/${tileKey} não encontrado`);
        return { type: 'FeatureCollection', features: [] };
    }
    
    return {
        type: 'FeatureCollection',
        features: tiles[tileKey]
    };
}
