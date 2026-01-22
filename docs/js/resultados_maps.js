// ============================================================
// RESULTADOS - JAVASCRIPT PARA MAPAS (Leaflet)
// ============================================================

// Variáveis globais para armazenar mapas e camadas
const mapInstances = {};
const dataLayers = {
    municipios: null,
    regioes: null,
    malhaVicinais: null
};

// Cores para visualizações
const colors = {
    faixas: {
        '0-20 km': '#ff6b6b',
        '20-40 km': '#4ecdc4',
        '40-60 km': '#ffe66d',
        '60-80 km': '#a8e6cf',
        '80-100 km': '#95a5a6',
        '100-150 km': '#3498db',
        '>150 km': '#9b59b6',
        'Sem dados': '#d3d3d3'
    },
    regioes: ['#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#e74c3c']
};

// Função auxiliar para criar mapa base
function createBaseMap(containerId, center = [-23.5, -48.5], zoom = 7) {
    const map = L.map(containerId, {
        center: center,
        zoom: zoom,
        zoomControl: true,
        scrollWheelZoom: true
    });

    // Adicionar tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);

    return map;
}

// Função para estilizar municípios por faixa de extensão
function getStyleByFaixa(feature) {
    const faixa = feature.properties.faixa_extensao || 'Sem dados';
    return {
        fillColor: colors.faixas[faixa] || '#d3d3d3',
        weight: 1,
        opacity: 1,
        color: '#666',
        fillOpacity: 0.7
    };
}

// Função auxiliar para decodificar nomes com acentos corretamente
function decodeText(text) {
    if (!text) return 'Sem nome';
    try {
        // Tenta decodificar se estiver em UTF-8 mal interpretado
        const decoded = decodeURIComponent(escape(text));
        return decoded;
    } catch (e) {
        return text;
    }
}

// Função para criar popup de município
function createMunicipioPopup(feature) {
    const props = feature.properties;
    const nomeMunicipio = decodeText(props.Municipio);
    return `
        <div class="popup-title">${nomeMunicipio}</div>
        <div class="popup-content">
            <div class="popup-item">
                <span class="popup-label">Extensão:</span> 
                <span class="popup-value">${(props.extensao_km || 0).toFixed(2)} km</span>
            </div>
            <div class="popup-item">
                <span class="popup-label">Segmentos:</span> 
                <span class="popup-value">${props.num_segmentos || 0}</span>
            </div>
            <div class="popup-item">
                <span class="popup-label">Faixa:</span> 
                <span class="popup-value">${props.faixa_extensao || 'Sem dados'}</span>
            </div>
        </div>
    `;
}

// Função para criar popup de região administrativa
function createRegiaoPopup(feature) {
    const props = feature.properties;
    const nomeRA = decodeText(props.RA);
    return `
        <div class="popup-title">${nomeRA}</div>
        <div class="popup-content">
            <div class="popup-item">
                <span class="popup-label">Extensão Total:</span> 
                <span class="popup-value">${(props.extensao_km || 0).toFixed(2)} km</span>
            </div>
            <div class="popup-item">
                <span class="popup-label">Segmentos:</span> 
                <span class="popup-value">${props.num_segmentos || 0}</span>
            </div>
        </div>
    `;
}

// Função para criar legenda de faixas de extensão
function createFaixasLegend(map) {
    const legend = L.control({position: 'bottomright'});
    
    legend.onAdd = function() {
        const div = L.DomUtil.create('div', 'map-legend');
        div.innerHTML = '<div class="map-legend-title">Extensão (km)</div>';
        
        const faixas = ['0-20 km', '20-40 km', '40-60 km', '60-80 km', '80-100 km', '100-150 km', '>150 km'];
        
        faixas.forEach(faixa => {
            div.innerHTML += `
                <div class="map-legend-item">
                    <span class="map-legend-color" style="background-color: ${colors.faixas[faixa]}"></span>
                    <span class="map-legend-label">${faixa}</span>
                </div>
            `;
        });
        
        return div;
    };
    
    legend.addTo(map);
}

// Mapa 1: Distribuição municipal por faixas de extensão
async function createMapFaixasExtensao() {
    const containerId = 'mapFaixasExtensao';
    const container = document.getElementById(containerId);
    if (!container) return;

    const map = createBaseMap(containerId);
    mapInstances[containerId] = map;

    try {
        // Carregar dados dos municípios com totais
        const response = await fetch('../data/municipios_totais.geojson');
        const data = await response.json();

        // Adicionar camada de municípios
        const geojsonLayer = L.geoJSON(data, {
            style: getStyleByFaixa,
            onEachFeature: function(feature, layer) {
                layer.bindPopup(createMunicipioPopup(feature));
                
                // Interatividade: destaque ao passar o mouse
                layer.on({
                    mouseover: function(e) {
                        const layer = e.target;
                        layer.setStyle({
                            weight: 3,
                            color: '#333',
                            fillOpacity: 0.9
                        });
                    },
                    mouseout: function(e) {
                        geojsonLayer.resetStyle(e.target);
                    }
                });
            }
        }).addTo(map);

        // Ajustar zoom para mostrar todas as features
        map.fitBounds(geojsonLayer.getBounds());

        // Adicionar legenda
        createFaixasLegend(map);

    } catch (error) {
        console.error('Erro ao carregar mapa de faixas de extensão:', error);
    }
}

// Mapa 2: Top 10 municípios com gradiente completo (maior e menor)
async function createMapTop10(tipo = 'maior') {
    const containerId = tipo === 'maior' ? 'mapTop10Maior' : 'mapTop10Menor';
    const container = document.getElementById(containerId);
    if (!container) return;

    const map = createBaseMap(containerId);
    mapInstances[containerId] = map;

    try {
        // Carregar dados
        const [municipiosResp, top10Resp] = await Promise.all([
            fetch('../data/municipios_totais.geojson'),
            fetch('../data/top10_municipios.json')
        ]);

        const municipios = await municipiosResp.json();
        const top10Data = await top10Resp.json();
        const top10List = top10Data[tipo];

        // Criar conjunto de códigos IBGE do top 10 para destaque
        const top10Codes = new Set(top10List.map(m => m.Cod_ibge));

        // Calcular min e max para gradiente
        const extensoes = municipios.features
            .map(f => f.properties.extensao_km || 0)
            .filter(e => e > 0);
        const minExt = Math.min(...extensoes);
        const maxExt = Math.max(...extensoes);

        // Função para calcular cor do gradiente
        function getGradientColor(extensao, tipo) {
            if (!extensao || extensao === 0) return '#e0e0e0';
            
            // Normalizar entre 0 e 1
            const normalized = (extensao - minExt) / (maxExt - minExt);
            
            if (tipo === 'maior') {
                // Verde claro -> Verde escuro (menor -> maior)
                const r = Math.round(144 - (normalized * 98));  // 144 -> 46
                const g = Math.round(238 - (normalized * 34));  // 238 -> 204
                const b = Math.round(144 - (normalized * 31));  // 144 -> 113
                return `rgb(${r}, ${g}, ${b})`;
            } else {
                // Vermelho claro -> Vermelho escuro (menor -> maior)
                const r = Math.round(255 - (normalized * 24));  // 255 -> 231
                const g = Math.round(205 - (normalized * 129)); // 205 -> 76
                const b = Math.round(210 - (normalized * 150)); // 210 -> 60
                return `rgb(${r}, ${g}, ${b})`;
            }
        }

        // Adicionar camada com TODOS os municípios coloridos por gradiente
        const gradientLayer = L.geoJSON(municipios, {
            style: function(feature) {
                const extensao = feature.properties.extensao_km || 0;
                const isTop10 = top10Codes.has(feature.properties.Cod_ibge);
                
                return {
                    fillColor: getGradientColor(extensao, tipo),
                    weight: isTop10 ? 2.5 : 1,
                    opacity: 1,
                    color: isTop10 ? '#000' : '#666',
                    fillOpacity: extensao > 0 ? 0.75 : 0.2
                };
            },
            onEachFeature: function(feature, layer) {
                const extensao = feature.properties.extensao_km || 0;
                if (extensao > 0) {
                    layer.bindPopup(createMunicipioPopup(feature));
                    
                    layer.on({
                        mouseover: function(e) {
                            e.target.setStyle({
                                weight: 3,
                                fillOpacity: 0.95
                            });
                        },
                        mouseout: function(e) {
                            const isTop10 = top10Codes.has(feature.properties.Cod_ibge);
                            e.target.setStyle({
                                weight: isTop10 ? 2.5 : 1,
                                fillOpacity: 0.75
                            });
                        }
                    });
                }
            }
        }).addTo(map);

        // Ajustar zoom
        map.fitBounds(gradientLayer.getBounds());
        
        // Adicionar legenda de gradiente
        const legend = L.control({position: 'bottomright'});
        legend.onAdd = function() {
            const div = L.DomUtil.create('div', 'map-legend');
            const titulo = tipo === 'maior' ? 'Extensão Vicinal (km)' : 'Extensão Vicinal (km)';
            div.innerHTML = `<div class="map-legend-title">${titulo}</div>`;
            
            const steps = [
                { value: maxExt, label: maxExt.toFixed(0) + ' km (máx)' },
                { value: maxExt * 0.75, label: (maxExt * 0.75).toFixed(0) + ' km' },
                { value: maxExt * 0.5, label: (maxExt * 0.5).toFixed(0) + ' km' },
                { value: maxExt * 0.25, label: (maxExt * 0.25).toFixed(0) + ' km' },
                { value: minExt, label: minExt.toFixed(0) + ' km (mín)' }
            ];
            
            steps.forEach(step => {
                const color = getGradientColor(step.value, tipo);
                div.innerHTML += `
                    <div class="map-legend-item">
                        <span class="map-legend-color" style="background: ${color};"></span>
                        <span class="map-legend-label">${step.label}</span>
                    </div>
                `;
            });
            
            div.innerHTML += `
                <div class="map-legend-item">
                    <span class="map-legend-color" style="background: #e0e0e0; border: 1px solid #999;"></span>
                    <span class="map-legend-label">Sem dados</span>
                </div>
            `;
            
            return div;
        };
        legend.addTo(map);

    } catch (error) {
        console.error(`Erro ao carregar mapa top 10 ${tipo}:`, error);
    }
}

// Mapa 3: Regiões Administrativas com gradiente completo
async function createMapRegioes() {
    const containerId = 'mapRegioesRA';
    const container = document.getElementById(containerId);
    if (!container) return;

    const map = createBaseMap(containerId);
    mapInstances[containerId] = map;

    try {
        // Carregar dados das regiões com totais
        const response = await fetch('../data/regioes_totais.geojson');
        const data = await response.json();

        // Ordenar regiões por extensão
        const features = data.features.sort((a, b) => 
            (b.properties.extensao_km || 0) - (a.properties.extensao_km || 0)
        );

        // Calcular min e max para gradiente
        const extensoes = features.map(f => f.properties.extensao_km || 0);
        const minExt = Math.min(...extensoes);
        const maxExt = Math.max(...extensoes);

        // Função para gerar cor do gradiente (azul para cinza)
        const getColorByGradient = (extensao) => {
            const normalized = (extensao - minExt) / (maxExt - minExt);
            const r = Math.round(52 + normalized * (149 - 52));   // 52 -> 149
            const g = Math.round(152 + normalized * (165 - 152)); // 152 -> 165
            const b = Math.round(219 + normalized * (166 - 219)); // 219 -> 166
            return `rgb(${r}, ${g}, ${b})`;
        };

        // Adicionar camada de regiões
        const layer = L.geoJSON(data, {
            style: function(feature) {
                const extensao = feature.properties.extensao_km || 0;
                return {
                    fillColor: getColorByGradient(extensao),
                    weight: 2,
                    opacity: 1,
                    color: '#333',
                    fillOpacity: 0.65
                };
            },
            onEachFeature: function(feature, layer) {
                layer.bindPopup(createRegiaoPopup(feature));
                
                layer.on({
                    mouseover: function(e) {
                        e.target.setStyle({
                            weight: 3,
                            fillOpacity: 0.8
                        });
                    },
                    mouseout: function(e) {
                        e.target.setStyle({
                            weight: 2,
                            fillOpacity: 0.65
                        });
                    }
                });
            }
        }).addTo(map);

        // Ajustar zoom
        map.fitBounds(layer.getBounds());

        // Adicionar legenda de gradiente
        const legend = L.control({position: 'bottomright'});
        legend.onAdd = function() {
            const div = L.DomUtil.create('div', 'map-legend');
            div.innerHTML = '<div class="map-legend-title">Extensão (km)</div>';
            
            // Criar gradiente de 5 níveis
            const steps = [
                { value: maxExt, label: maxExt.toFixed(0) + ' km (máx)' },
                { value: maxExt * 0.75, label: (maxExt * 0.75).toFixed(0) + ' km' },
                { value: maxExt * 0.5, label: (maxExt * 0.5).toFixed(0) + ' km' },
                { value: maxExt * 0.25, label: (maxExt * 0.25).toFixed(0) + ' km' },
                { value: minExt, label: minExt.toFixed(0) + ' km (mín)' }
            ];
            
            steps.forEach(step => {
                const color = getColorByGradient(step.value);
                div.innerHTML += `
                    <div class="map-legend-item">
                        <span class="map-legend-color" style="background-color: ${color}"></span>
                        <span class="map-legend-label">${step.label}</span>
                    </div>
                `;
            });
            
            return div;
        };
        legend.addTo(map);

    } catch (error) {
        console.error('Erro ao carregar mapa de regiões:', error);
    }
}

// Inicializar todos os mapas quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    createMapFaixasExtensao();
    createMapTop10('maior');
    createMapTop10('menor');
    createMapRegioes();
});

// Função para redimensionar mapas quando a janela muda de tamanho
window.addEventListener('resize', function() {
    Object.values(mapInstances).forEach(map => {
        if (map) {
            map.invalidateSize();
        }
    });
});
