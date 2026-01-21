// ============================================================================
// MAPAS COMPLETOS - Canvas Renderer + Controles de Camadas
// ============================================================================

let malhaVicinais = null;
let malhaDER = null;
let malhaEstadual = null;
let areasUrbanizadas = null;
let municipios = null;
let regioes = null;
let indicadores = null;
let mapasCarregados = {};

const canvasRenderer = L.canvas({ padding: 0.5 });

// ============================================================================
// BASEMAPS
// ============================================================================
const baseMaps = {
    'OpenStreetMap': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }),
    'Esri Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: '© Esri'
    }),
    'Esri Topo': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: '© Esri'
    }),
    'CartoDB Light': L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '© CartoDB'
    }),
    'CartoDB Dark': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '© CartoDB'
    })
};

// ============================================================================
// CARREGAR DADOS
// ============================================================================
const fetchCacheOptions = {cache: 'force-cache'};
const fetchJson = (url) => fetch(url, fetchCacheOptions).then(r => r.json());

fetchJson('../data/indicadores.json')
    .then(ind => {
        indicadores = ind;
        console.log(`✓ Indicadores carregados`);
    });

function carregarVicinais() {
    if (malhaVicinais) return Promise.resolve(malhaVicinais);
    console.log('Carregando Rodovias Municipais (7.417 segmentos)...');
    return fetchJson('../data/malha_osm.geojson')
        .then(data => {
            malhaVicinais = data;
            console.log(`✓ Rodovias Municipais: ${data.features.length} segmentos`);
            return data;
        });
}

function carregarDER() {
    if (malhaDER) return Promise.resolve(malhaDER);
    console.log('Carregando DER (379.742 segmentos)...');
    return fetchJson('../data/malha_der.geojson')
        .then(data => {
            malhaDER = data;
            console.log(`✓ DER: ${data.features.length} segmentos`);
            return data;
        });
}

function carregarMunicipios() {
    if (municipios) return Promise.resolve(municipios);
    console.log('Carregando municípios...');
    return fetchJson('../data/municipios_sp.geojson')
        .then(data => {
            municipios = data;
            console.log(`✓ Municípios: ${data.features.length} polígonos`);
            return data;
        });
}

function carregarRegioes() {
    if (regioes) return Promise.resolve(regioes);
    console.log('Carregando regiões administrativas...');
    return fetchJson('../data/regioes_administrativas_sp.geojson')
        .then(data => {
            regioes = data;
            console.log(`✓ Regiões: ${data.features.length} polígonos`);
            return data;
        });
}

function carregarMalhaEstadual() {
    if (malhaEstadual) return Promise.resolve(malhaEstadual);
    console.log('Carregando malha estadual DER...');
    return fetchJson('../data/malha_estadual_der.geojson')
        .then(data => {
            malhaEstadual = data;
            console.log(`✓ Malha Estadual: ${data.features.length} segmentos`);
            return data;
        });
}

function carregarAreasUrbanizadas() {
    if (areasUrbanizadas) return Promise.resolve(areasUrbanizadas);
    console.log('Carregando áreas urbanizadas...');
    return fetchJson('../data/areas_urbanizadas_ibge.geojson')
        .then(data => {
            areasUrbanizadas = data;
            console.log(`✓ Áreas Urbanizadas: ${data.features.length} polígonos`);
            return data;
        });
}

// ============================================================================
// CRIAR MAPA GENÉRICO COM CAMADAS
// ============================================================================
function criarMapaComCamadas(mapId, malhaConfig) {
    if (mapasCarregados[mapId]) return;
    
    const map = L.map(mapId, {preferCanvas: true}).setView([-22.5, -48.5], 7);
    baseMaps['OpenStreetMap'].addTo(map);
    
    // Loading
    const loading = L.control({position: 'topright'});
    loading.onAdd = function() {
        this._div = L.DomUtil.create('div', 'info');
        this._div.innerHTML = '<h4>⏳ Carregando...</h4>';
        return this._div;
    };
    loading.addTo(map);
    
    const camadas = {};
    
    // Carregar todas as camadas
    Promise.all([
        carregarVicinais(),
        carregarDER(),
        carregarMunicipios(),
        carregarRegioes(),
        carregarMalhaEstadual(),
        carregarAreasUrbanizadas()
    ]).then(([vicinais, der, mun, reg, estadual, au]) => {
        map.removeControl(loading);
        
        // Camada de Áreas Urbanizadas
        camadas.areasUrbanizadas = L.geoJSON(au, {
            renderer: canvasRenderer,
            style: {
                color: '#FF0000',
                weight: 1,
                fillColor: '#FF0000',
                fillOpacity: 0.1,
                opacity: 0.3
            },
            interactive: false
        });
        
        // Camada de Malha Estadual
        camadas.malhaEstadual = L.geoJSON(estadual, {
            renderer: canvasRenderer,
            style: {
                color: '#FF9900',
                weight: 2,
                opacity: 0.7
            },
            interactive: false
        });
        
        // Camada de Regiões Administrativas
        camadas.regioes = L.geoJSON(reg, {
            renderer: canvasRenderer,
            style: {
                color: '#9C27B0',
                weight: 2,
                fill: false,
                opacity: 0.7
            },
            interactive: false
        });
        
        // Camada de Municípios
        camadas.municipios = L.geoJSON(mun, {
            renderer: canvasRenderer,
            style: {
                color: '#666',
                weight: 1,
                fill: false,
                opacity: 0.4
            },
            interactive: false
        });
        
        // Camada de Vicinais ou DER
        if (malhaConfig.tipo === 'vicinais') {
            camadas.malha = L.geoJSON(vicinais, {
                renderer: canvasRenderer,
                style: feature => malhaConfig.style(feature),
                interactive: false
            });
        } else if (malhaConfig.tipo === 'der') {
            camadas.malha = L.geoJSON(der, {
                renderer: canvasRenderer,
                style: feature => malhaConfig.style(feature),
                interactive: false
            });
        } else if (malhaConfig.tipo === 'comparacao') {
            // Duas camadas
            camadas.malhaVic = L.geoJSON(vicinais, {
                renderer: canvasRenderer,
                style: {color: '#0066CC', weight: 0.8, opacity: 0.4},
                interactive: false
            });
            camadas.malhaDER = L.geoJSON(der, {
                renderer: canvasRenderer,
                style: {color: '#FF6600', weight: 1.2, opacity: 0.7},
                interactive: false
            });
        }
        
        // Adicionar camadas ao mapa
        if (camadas.areasUrbanizadas) camadas.areasUrbanizadas.addTo(map);
        if (camadas.malhaEstadual) camadas.malhaEstadual.addTo(map);
        if (camadas.regioes) camadas.regioes.addTo(map);
        if (camadas.municipios) camadas.municipios.addTo(map);
        if (camadas.malha) camadas.malha.addTo(map);
        if (camadas.malhaVic) camadas.malhaVic.addTo(map);
        if (camadas.malhaDER) camadas.malhaDER.addTo(map);
        
        // Controle de Basemaps
        L.control.layers(baseMaps, null, {position: 'topleft'}).addTo(map);
        
        // Controle de Camadas (checkboxes) com ordem inicial por tipo (vetor/raster) e alfabética
        const overlayItems = [];
        overlayItems.push({key: 'au', label: 'Áreas Urbanizadas', type: 'vector', symbol: 'symbol-polygon symbol-au'});
        overlayItems.push({key: 'estadual', label: 'Malha Estadual DER', type: 'vector', symbol: 'symbol-line symbol-estadual'});
        overlayItems.push({key: 'regioes', label: 'Regiões Administrativas', type: 'vector', symbol: 'symbol-line symbol-regioes'});
        overlayItems.push({key: 'municipios', label: 'Municípios', type: 'vector', symbol: 'symbol-line symbol-municipios'});
        if (malhaConfig.tipo === 'comparacao') {
            overlayItems.push({key: 'vicinais', label: 'Vicinais', type: 'vector', symbol: 'symbol-line symbol-vicinais'});
            overlayItems.push({key: 'der', label: 'DER', type: 'vector', symbol: 'symbol-line symbol-der'});
        } else {
            const symbolClass = malhaConfig.tipo === 'der' ? 'symbol-line symbol-der' : 'symbol-line symbol-vicinais';
            overlayItems.push({key: 'malha', label: malhaConfig.label, type: 'vector', symbol: symbolClass});
        }
        const typeOrder = {vector: 0, raster: 1};
        overlayItems.sort((a, b) => {
            const ta = typeOrder[a.type] ?? 9;
            const tb = typeOrder[b.type] ?? 9;
            if (ta !== tb) return ta - tb;
            return a.label.localeCompare(b.label, 'pt-BR');
        });

        const layerControl = L.control({position: 'topleft'});
        layerControl.onAdd = function() {
            this._div = L.DomUtil.create('div', 'layer-control');
            this._div.innerHTML = `
                <h4>Camadas</h4>
                <ul class="layer-list" id="${mapId}-layer-list">
                    ${overlayItems.map(item => `
                        <li class="layer-item" data-key="${item.key}" draggable="true">
                            <label>
                                <span class="layer-symbol ${item.symbol}"></span>
                                <input type="checkbox" id="${mapId}-chk-${item.key}" checked>
                                <span class="layer-label">${item.label}</span>
                            </label>
                        </li>
                    `).join('')}
                </ul>
            `;
            return this._div;
        };
        layerControl.addTo(map);
        
        // Event listeners para checkboxes e ordenação dinâmica por arrastar/soltar
        setTimeout(() => {
            const overlayLayers = {
                au: camadas.areasUrbanizadas,
                estadual: camadas.malhaEstadual,
                regioes: camadas.regioes,
                municipios: camadas.municipios,
                malha: camadas.malha,
                vicinais: camadas.malhaVic,
                der: camadas.malhaDER
            };

            const getCurrentOrder = () => {
                const list = document.getElementById(`${mapId}-layer-list`);
                if (!list) return [];
                return Array.from(list.querySelectorAll('.layer-item')).map(li => li.dataset.key);
            };

            const applyOverlayOrder = (order) => {
                const keys = (order && order.length) ? order : getCurrentOrder();
                const reversed = keys.slice().reverse();
                reversed.forEach(key => {
                    const layer = overlayLayers[key];
                    if (layer && map.hasLayer(layer) && typeof layer.bringToFront === 'function') {
                        layer.bringToFront();
                    }
                });
            };

            const defer = window.requestIdleCallback
                ? (cb) => window.requestIdleCallback(cb, {timeout: 300})
                : (cb) => setTimeout(cb, 0);

            const toggleLayer = (key, checked) => {
                const layer = overlayLayers[key];
                if (!layer) return;
                defer(() => {
                    if (checked) {
                        layer.addTo(map);
                    } else {
                        layer.remove();
                    }
                    applyOverlayOrder();
                });
            };

            document.getElementById(`${mapId}-chk-au`)?.addEventListener('change', e => {
                toggleLayer('au', e.target.checked);
            });
            document.getElementById(`${mapId}-chk-estadual`)?.addEventListener('change', e => {
                toggleLayer('estadual', e.target.checked);
            });
            document.getElementById(`${mapId}-chk-regioes`)?.addEventListener('change', e => {
                toggleLayer('regioes', e.target.checked);
            });
            document.getElementById(`${mapId}-chk-municipios`)?.addEventListener('change', e => {
                toggleLayer('municipios', e.target.checked);
            });
            if (malhaConfig.tipo === 'comparacao') {
                document.getElementById(`${mapId}-chk-vicinais`)?.addEventListener('change', e => {
                    toggleLayer('vicinais', e.target.checked);
                });
                document.getElementById(`${mapId}-chk-der`)?.addEventListener('change', e => {
                    toggleLayer('der', e.target.checked);
                });
            } else {
                document.getElementById(`${mapId}-chk-malha`)?.addEventListener('change', e => {
                    toggleLayer('malha', e.target.checked);
                });
            }

            // Drag & drop para reordenar camadas (ordem do controle = ordem no mapa)
            const list = document.getElementById(`${mapId}-layer-list`);
            if (list) {
                let dragged = null;
                list.addEventListener('dragstart', e => {
                    const item = e.target.closest('.layer-item');
                    if (!item) return;
                    dragged = item;
                    item.classList.add('dragging');
                    e.dataTransfer.effectAllowed = 'move';
                });
                list.addEventListener('dragover', e => {
                    const item = e.target.closest('.layer-item');
                    if (!item || item === dragged) return;
                    e.preventDefault();
                    const rect = item.getBoundingClientRect();
                    const next = (e.clientY - rect.top) > rect.height / 2;
                    list.insertBefore(dragged, next ? item.nextSibling : item);
                });
                list.addEventListener('drop', e => {
                    e.preventDefault();
                    if (dragged) dragged.classList.remove('dragging');
                    dragged = null;
                    applyOverlayOrder();
                });
                list.addEventListener('dragend', () => {
                    if (dragged) dragged.classList.remove('dragging');
                    dragged = null;
                });
            }

            // Aplicar ordem inicial (vetor -> raster, alfabética)
            applyOverlayOrder();
        }, 50); // Timeout reduzido para melhor performance
        
        // Legenda
        if (malhaConfig.legend) {
            const legend = L.control({position: 'bottomright'});
            legend.onAdd = function() {
                const div = L.DomUtil.create('div', 'legend');
                div.innerHTML = malhaConfig.legend;
                return div;
            };
            legend.addTo(map);
        }
        
        // Info
        if (malhaConfig.info) {
            const info = L.control({position: 'topright'});
            info.onAdd = function() {
                this._div = L.DomUtil.create('div', 'info');
                this._div.innerHTML = malhaConfig.info;
                return this._div;
            };
            info.addTo(map);
        }
        
        mapasCarregados[mapId] = true;
        console.log(`✓ ${mapId} renderizado`);
    });
}

// ============================================================================
// MAPA 1: Vicinais por tipo de superfície
// ============================================================================
function criarMapa1() {
    criarMapaComCamadas('mapa1', {
        tipo: 'vicinais',
        label: 'Rodovias Municipais',
        style: feature => {
            const cores = {
                '1': '#D32F2F', '2': '#FF9800', '3': '#4CAF50',
                '4': '#2196F3', '5': '#9C27B0', '6': '#FFC107'
            };
            return {
                color: cores[feature.properties.sup_tipo_c] || '#888',
                weight: 1,
                opacity: 0.6
            };
        },
        legend: `
            <h4>Tipo de Superfície</h4>
            <div><i style="background:#D32F2F"></i> Tipo 1</div>
            <div><i style="background:#FF9800"></i> Tipo 2</div>
            <div><i style="background:#4CAF50"></i> Tipo 3</div>
            <div><i style="background:#2196F3"></i> Tipo 4</div>
        `,
        info: `
            <h4>Rodovias Municipais por Superfície</h4>
            <strong>${indicadores?.osm?.extensao_km?.toLocaleString('pt-BR') || '...'} km</strong><br/>
            <strong>${indicadores?.osm?.segmentos?.toLocaleString('pt-BR') || '...'} segmentos</strong>
        `
    });
}

// ============================================================================
// MAPA 2: Vicinais com/sem nome
// ============================================================================
function criarMapa2() {
    criarMapaComCamadas('mapa2', {
        tipo: 'vicinais',
        label: 'Rodovias Municipais',
        style: feature => {
            const comNome = feature.properties.rod_munici && feature.properties.rod_munici.trim() !== '';
            return {
                color: comNome ? '#2E7D32' : '#BDBDBD',
                weight: comNome ? 1.5 : 0.5,
                opacity: comNome ? 0.7 : 0.3
            };
        },
        legend: `
            <h4>Identificação</h4>
            <div><i style="background:#2E7D32"></i> Com nome</div>
            <div><i style="background:#BDBDBD"></i> Sem nome</div>
        `,
        info: '<h4>Rodovias Municipais - Identificação</h4>'
    });
}

// ============================================================================
// MAPA 3: Vicinais por comprimento
// ============================================================================
function criarMapa3() {
    criarMapaComCamadas('mapa3', {
        tipo: 'vicinais',
        label: 'Rodovias Municipais',
        style: feature => {
            const km = (feature.properties.metros || 0) / 1000;
            const color = km > 5   ? '#b2182b' :
                         km > 2   ? '#ef8a62' :
                         km > 1   ? '#fddbc7' :
                         km > 0.5 ? '#d1e5f0' : '#2166ac';
            return {color, weight: 1, opacity: 0.6};
        },
        legend: `
            <h4>Comprimento</h4>
            <div><i style="background:#b2182b"></i> > 5 km</div>
            <div><i style="background:#ef8a62"></i> 2-5 km</div>
            <div><i style="background:#fddbc7"></i> 1-2 km</div>
            <div><i style="background:#d1e5f0"></i> 0.5-1 km</div>
            <div><i style="background:#2166ac"></i> < 0.5 km</div>
        `,
        info: '<h4>Rodovias Municipais por Comprimento</h4>'
    });
}

// ============================================================================
// MAPA 4: Vicinais por tipo de superfície (repetido)
// ============================================================================
function criarMapa4() {
    criarMapaComCamadas('mapa4', {
        tipo: 'vicinais',
        label: 'Rodovias Municipais',
        style: feature => {
            const cores = {
                '1': '#4CAF50', '2': '#2196F3', '3': '#D32F2F',
                '4': '#FF9800', '5': '#795548'
            };
            return {
                color: cores[feature.properties.sup_tipo_c] || '#888',
                weight: 1,
                opacity: 0.6
            };
        },
        legend: `
            <h4>Superfície</h4>
            <div><i style="background:#4CAF50"></i> Tipo 1</div>
            <div><i style="background:#2196F3"></i> Tipo 2</div>
            <div><i style="background:#D32F2F"></i> Tipo 3</div>
            <div><i style="background:#FF9800"></i> Tipo 4</div>
        `,
        info: '<h4>Rodovias Municipais - Superfície</h4>'
    });
}

// ============================================================================
// MAPA 5: DER completa
// ============================================================================
function criarMapa5() {
    criarMapaComCamadas('mapa5', {
        tipo: 'der',
        label: 'Malha DER',
        style: () => ({color: '#FF6600', weight: 1, opacity: 0.6}),
        info: `
            <h4>Malha DER Completa</h4>
            <strong>${indicadores?.der?.extensao_km?.toLocaleString('pt-BR') || '...'} km</strong><br/>
            <strong>${indicadores?.der?.segmentos?.toLocaleString('pt-BR') || '...'} segmentos</strong>
        `
    });
}

// ============================================================================
// MAPA 6: DER por tipo
// ============================================================================
function criarMapa6() {
    criarMapaComCamadas('mapa6', {
        tipo: 'der',
        label: 'Malha DER',
        style: feature => {
            const cores = {
                'track': '#D32F2F',
                'unclassified': '#FF9800',
                'residential': '#4CAF50',
                'service': '#2196F3'
            };
            return {
                color: cores[feature.properties.tipo_osm] || '#888',
                weight: 1,
                opacity: 0.6
            };
        },
        legend: `
            <h4>Tipo de Via (DER)</h4>
            <div><i style="background:#D32F2F"></i> Track</div>
            <div><i style="background:#FF9800"></i> Unclassified</div>
            <div><i style="background:#4CAF50"></i> Residential</div>
        `,
        info: '<h4>Malha DER por Tipo</h4>'
    });
}

// ============================================================================
// MAPA 7: Comparação
// ============================================================================
function criarMapa7() {
    criarMapaComCamadas('mapa7', {
        tipo: 'comparacao',
        legend: `
            <h4>Comparação</h4>
            <div><i style="background:#0066CC"></i> Municipais (${indicadores?.osm?.extensao_km?.toLocaleString('pt-BR') || '...'} km)</div>
            <div><i style="background:#FF6600"></i> DER (${indicadores?.der?.extensao_km?.toLocaleString('pt-BR') || '...'} km)</div>
        `,
        info: '<h4>Comparação Vicinais x DER</h4>'
    });
}

// ============================================================================
// MAPA 8: Gap
// ============================================================================
function criarMapa8() {
    criarMapaComCamadas('mapa8', {
        tipo: 'der',
        label: 'Gap de Cobertura',
        style: () => ({color: '#FF6600', weight: 1.5, opacity: 0.8}),
        info: () => {
            const gap = (indicadores?.der?.extensao_km || 0) - (indicadores?.osm?.extensao_km || 0);
            const razao = ((indicadores?.der?.extensao_km || 0) / (indicadores?.osm?.extensao_km || 1)).toFixed(1);
            return `
                <h4>Gap de Cobertura</h4>
                <strong style="color:#FF6600">${Math.abs(gap).toLocaleString('pt-BR')} km</strong><br/>
                Razão DER/Municipais: <strong>${razao}×</strong>
            `;
        }
    });
}

// ============================================================================
// LAZY LOADING
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('✓ Sistema pronto');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const mapId = entry.target.id;
                const funcName = `criarMapa${mapId.replace('mapa', '')}`;
                if (window[funcName]) {
                    console.log(`→ Inicializando ${mapId}...`);
                    window[funcName]();
                    observer.unobserve(entry.target);
                }
            }
        });
    }, {rootMargin: '300px'});
    
    for (let i = 1; i <= 8; i++) {
        const el = document.getElementById(`mapa${i}`);
        if (el) observer.observe(el);
    }
});

window.criarMapa1 = criarMapa1;
window.criarMapa2 = criarMapa2;
window.criarMapa3 = criarMapa3;
window.criarMapa4 = criarMapa4;
window.criarMapa5 = criarMapa5;
window.criarMapa6 = criarMapa6;
window.criarMapa7 = criarMapa7;
window.criarMapa8 = criarMapa8;
