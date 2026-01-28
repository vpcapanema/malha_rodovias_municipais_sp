/**
 * resultados_municipal.js
 * Script completo para página de resultados municipais
 * Carrega dados reais IBGE 2025 e cria todas as visualizações
 */

// Dados globais
let dadosMunicipios = [];
let dadosRegioes = [];
let dadosEstatisticas = {};
let dadosSegmentos = {};

// Dados da malha total (OSM + DER)
let dadosMunicipiosTotal = [];
let dadosRegioesTotal = [];
let dadosEstatisticasTotal = {};
let dadosPavimentacao = {};
let dadosSegmentosTotal = {}; // Estatísticas de segmentos da malha total
let malhaTotalTilesInfo = null;

// Estado do toggle de visualização
let visualizacaoAtual = 'osm'; // 'osm' ou 'total'

// Cache para acelerar joins por código IBGE
let _dadosMunicipiosPorCodigoIbge = null;

// Flag para evitar inicialização múltipla
let paginaInicializada = false;

// Cache de mapas Leaflet (usa o cache global inicializado no HTML)
const mapasLeaflet = window.mapasLeaflet || {};

// Referências aos gráficos Chart.js para destruição
let chartComprimentoSegmentos = null;
let chartTipoPavimento = null;
let chartFaixasExtensao = null;
let chartTop10Maior = null;
let chartTop10Menor = null;
let chartDensidadeArea = null;
let chartDensidadePop = null;
let chartDisparidadeArea = null;
let chartDisparidadePop = null;

function formatDecimal(value, { digits = 2, fallback = 'N/D' } = {}) {
    if (typeof value === 'number' && Number.isFinite(value)) {
        return value.toLocaleString('pt-BR', {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits
        });
    }
    return fallback;
}

/**
 * Calcula o desvio padrão de um array de valores numéricos
 */
function calcularDesvioPadrao(valores) {
    const nums = valores.filter(v => typeof v === 'number' && Number.isFinite(v));
    if (nums.length === 0) return null;
    const media = nums.reduce((a, b) => a + b, 0) / nums.length;
    const somaQuadrados = nums.reduce((sum, v) => sum + Math.pow(v - media, 2), 0);
    return Math.sqrt(somaQuadrados / nums.length);
}

/**
 * Calcula quebras por quantis para classificação coroplética
 * Distribui os valores em classes com aproximadamente o mesmo número de observações
 * @param {number[]} valores - Array de valores numéricos
 * @param {number} numClasses - Número de classes desejadas (padrão: 5)
 * @returns {number[]} Array de quebras (tamanho = numClasses + 1, incluindo min e max)
 */
function calcularQuantis(valores, numClasses = 5) {
    const nums = valores.filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    if (nums.length === 0) return [];
    
    // Ordenar valores
    const sorted = [...nums].sort((a, b) => a - b);
    const n = sorted.length;
    
    const breaks = [sorted[0]]; // Começa com o mínimo
    
    for (let i = 1; i < numClasses; i++) {
        // Índice do quantil
        const idx = Math.floor((i / numClasses) * n);
        breaks.push(sorted[Math.min(idx, n - 1)]);
    }
    
    breaks.push(sorted[n - 1]); // Termina com o máximo
    
    return breaks;
}

function descricaoTipoPavimento(tipo) {
    const t = String(tipo ?? '').trim();
    const map = {
        '9': 'Terra/Cascalho (não pavimentado)',
        '8': 'Asfalto/Pavimentado',
        '7': 'Outros',
        '0': 'Não classificado',
        '1': 'Outros (tipo 1)',
        '2': 'Outros (tipo 2)'
    };
    return map[t] || 'Outros';
}

function corTipoPavimento(tipo) {
    const t = String(tipo ?? '').trim();
    const cores = {
        '9': '#FF8C00',
        '8': '#3498db',
        '7': '#1abc9c',
        '0': '#95a5a6',
        '1': '#9b59b6',
        '2': '#8e44ad'
    };
    return cores[t] || '#888888';
}

function getLegendaContainer(mapId) {
    // Primeiro tenta encontrar legenda existente pelo ID
    let el = document.getElementById(`legenda-${mapId}`);
    if (el) return el;
    
    // Se não existir, cria dentro do container do mapa
    const mapContainer = document.getElementById(mapId);
    if (!mapContainer) return null;
    
    // Procurar o parent .mapa-container ou usar o próprio mapa
    const parentContainer = mapContainer.closest('.mapa-container') || mapContainer.parentElement;
    if (!parentContainer) return null;
    
    // Criar elemento de legenda
    el = document.createElement('div');
    el.id = `legenda-${mapId}`;
    el.className = 'mapa-legenda-externa';
    el.setAttribute('aria-label', 'Legenda do mapa');
    
    // Inserir dentro do container do mapa (não depois)
    parentContainer.style.position = 'relative';
    parentContainer.appendChild(el);
    
    return el;
}

/**
 * Bounds padrão do estado de SP
 */
const BOUNDS_SP_PADRAO = [[-25.3, -53.2], [-19.7, -44.0]];
const CENTER_SP = [-22.5, -48.5];

/**
 * IDs de todos os mapas da página
 */
const MAPA_IDS = [
    'mapaMalhaCompleta',
    'mapaPavimento', 
    'mapaRankingExtensao',
    'mapaDensidadeArea',
    'mapaDensidadePop',
    'mapaTop10Maior',
    'mapaTop10Menor',
    'mapaDisparidadesArea',
    'mapaDisparidadesPop'
];

/**
 * Inicializa todos os mapas instantaneamente com basemap
 * Verifica se já foram inicializados pelo HTML inline
 */
function inicializarMapasInstantaneo() {
    console.log('🗺️ Verificando mapas pré-inicializados...');
    
    MAPA_IDS.forEach(mapId => {
        // Se já foi inicializado pelo HTML, apenas mostrar loading
        if (mapasLeaflet[mapId]) {
            console.log(`  ✓ ${mapId} já inicializado`);
            mostrarCarregamento(mapId, 'Carregando dados...', 'Aguarde');
            return;
        }
        
        const element = document.getElementById(mapId);
        if (!element) return;
        
        // Limpar mapa anterior se existir
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        
        try {
            const map = L.map(mapId, { 
                preferCanvas: true, 
                zoomControl: false,
                attributionControl: true
            });
            
            // Adicionar basemap padrão imediatamente
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(map);
            
            // Enquadrar no estado de SP
            map.fitBounds(BOUNDS_SP_PADRAO);
            
            // Salvar no cache
            mapasLeaflet[mapId] = map;
            
            // Mostrar loading
            mostrarCarregamento(mapId, 'Carregando dados...', 'Aguarde');
            
        } catch (err) {
            console.warn(`⚠️ Erro ao inicializar mapa ${mapId}:`, err);
        }
    });
    
    console.log(`✅ ${Object.keys(mapasLeaflet).length} mapas pré-inicializados`);
}

/**
 * Obtém mapa do cache ou cria novo se não existir
 */
function obterOuCriarMapa(mapId, options = {}) {
    if (mapasLeaflet[mapId]) {
        return mapasLeaflet[mapId];
    }
    
    const element = document.getElementById(mapId);
    if (!element) return null;
    
    // Limpar se já existe
    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = '';
    }
    
    const map = L.map(mapId, { 
        preferCanvas: options.preferCanvas !== false, 
        zoomControl: options.zoomControl || false,
        ...options
    });
    
    mapasLeaflet[mapId] = map;
    return map;
}

/**
 * Cria indicador de carregamento sobre o mapa
 */
function mostrarCarregamento(mapId, mensagem = 'Carregando...') {
    const container = document.getElementById(mapId);
    if (!container) return;

    // Remover loading anterior se existir
    const existente = container.querySelector('.map-loading-overlay');
    if (existente) existente.remove();
    
    const overlay = document.createElement('div');
    overlay.className = 'map-loading-overlay';
    overlay.innerHTML = `
        <div class="map-loading-content">
            <div class="map-loading-spinner"></div>
            <div class="map-loading-message">${mensagem}</div>
            <div class="map-loading-details"></div>
        </div>
    `;
    container.appendChild(overlay);
}

/**
 * Atualiza mensagem do indicador de carregamento
 */
function atualizarCarregamento(mapId, mensagem, detalhes = '') {
    const container = document.getElementById(mapId);
    if (!container) return;
    
    const overlay = container.querySelector('.map-loading-overlay');
    if (!overlay) return;
    
    const msgEl = overlay.querySelector('.map-loading-message');
    const detailsEl = overlay.querySelector('.map-loading-details');
    
    if (msgEl) msgEl.textContent = mensagem;
    if (detailsEl) detailsEl.textContent = detalhes;
}

/**
 * Remove indicador de carregamento
 */
function removerCarregamento(mapId) {
    const container = document.getElementById(mapId);
    if (!container) return;
    
    const overlay = container.querySelector('.map-loading-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 300);
    }
}

function renderLegendaExterna(mapId, titulo, items) {
    const el = getLegendaContainer(mapId);
    if (!el) {
        console.warn(`Container de legenda não encontrado para ${mapId}`);
        return;
    }

    // Sempre layout vertical com 1 coluna
    const safeItems = Array.isArray(items) ? items.filter(Boolean) : [];
    el.style.setProperty('--legend-cols', '1');

    const tituloHtml = titulo ? `<div class="legenda-titulo">${titulo}</div>` : '';
    const gridItemsHtml = safeItems.map(it => {
        const tipo = it?.tipo || 'fill'; // fill | line
        const cor = it?.color || '#888888';
        const label = it?.label ?? '';
        if (tipo === 'line') {
            return `
                <div class="legenda-item" title="${label}">
                    <span class="legenda-linha" style="color:${cor}"></span>
                    <span class="legenda-label">${label}</span>
                </div>
            `;
        }
        return `
            <div class="legenda-item" title="${label}">
                <span class="legenda-cor" style="background:${cor}"></span>
                <span class="legenda-label">${label}</span>
            </div>
        `;
    }).join('');

    el.innerHTML = `${tituloHtml}<div class="legenda-grid legenda-vertical">${gridItemsHtml}</div>`;
}

function renderLegendaGradienteExterna(mapId, titulo, minVal, maxVal, options = {}) {
    const el = getLegendaContainer(mapId);
    if (!el) {
        console.warn(`Container de legenda não encontrado para ${mapId}`);
        return;
    }

    const fromColor = options.fromColor || '#ffffcc';
    const toColor = options.toColor || '#253494';
    const unidade = options.unidade || '';
    const orientation = options.orientation || 'horizontal';
    const isVertical = orientation === 'vertical';
    const unitLabel = unidade ? ` ${unidade}` : '';

    const fmt = (v) => {
        if (typeof v !== 'number' || !Number.isFinite(v)) return 'N/A';
        return v.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    };

    const tituloHtml = titulo ? `<div class="legenda-titulo">${titulo}</div>` : '';
    const gradientDirection = isVertical ? 'to bottom' : 'to right';
    const gradientClass = isVertical ? ' legenda-gradiente-vertical' : '';
    const gradientBarClass = isVertical ? ' legenda-gradiente-bar-vertical' : '';
    
    // Para vertical: barra à esquerda, valores à direita (max no topo, min embaixo)
    // Para horizontal: min à esquerda, max à direita
    const gradHtml = isVertical ? `
        <div class="legenda-gradiente${gradientClass}">
            <div class="legenda-gradiente-bar${gradientBarClass}" style="background: linear-gradient(${gradientDirection}, ${toColor}, ${fromColor});"></div>
            <div class="legenda-valores-lateral">
                <span class="legenda-valor-max">${fmt(maxVal)}</span>
                <span class="legenda-valor-min">${fmt(minVal)}</span>
            </div>
        </div>
    ` : `
        <div class="legenda-gradiente">
            <div class="legenda-gradiente-labels">
                <span>${fmt(minVal)}</span>
                <span>${fmt(maxVal)}</span>
            </div>
            <div class="legenda-gradiente-bar" style="background: linear-gradient(${gradientDirection}, ${fromColor}, ${toColor});"></div>
        </div>
    `;

    el.style.setProperty('--legend-cols', '1');
    el.innerHTML = `${tituloHtml}${gradHtml}`;
}

function hexToRgb(hex) {
    const clean = String(hex || '').replace('#', '');
    if (clean.length !== 6) return { r: 0, g: 0, b: 0 };
    return {
        r: parseInt(clean.slice(0, 2), 16),
        g: parseInt(clean.slice(2, 4), 16),
        b: parseInt(clean.slice(4, 6), 16)
    };
}

function rgbToHex({ r, g, b }) {
    const toHex = (n) => {
        const v = Math.max(0, Math.min(255, Math.round(n)));
        return v.toString(16).padStart(2, '0');
    };
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function interpolarHex(a, b, t) {
    const tClamped = Math.max(0, Math.min(1, t));
    const ca = hexToRgb(a);
    const cb = hexToRgb(b);
    return rgbToHex({
        r: ca.r + (cb.r - ca.r) * tClamped,
        g: ca.g + (cb.g - ca.g) * tClamped,
        b: ca.b + (cb.b - ca.b) * tClamped
    });
}

/**
 * Cria uma função que mapeia valores para posição percentil (0-1)
 * Melhora contraste distribuindo valores uniformemente no gradiente
 * @param {number[]} valores - Array de todos os valores do dataset
 * @returns {function} Função que recebe um valor e retorna sua posição percentil (0-1)
 */
function criarMapeadorPercentil(valores) {
    const nums = valores.filter(v => typeof v === 'number' && Number.isFinite(v));
    if (nums.length === 0) return () => 0.5;
    
    // Ordenar valores e criar lookup
    const sorted = [...nums].sort((a, b) => a - b);
    const n = sorted.length;
    
    return (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return 0.5;
        
        // Encontrar posição do valor no array ordenado (busca binária aproximada)
        let low = 0, high = n - 1;
        while (low < high) {
            const mid = Math.floor((low + high) / 2);
            if (sorted[mid] < valor) low = mid + 1;
            else high = mid;
        }
        
        // Retornar posição como percentil (0 a 1)
        return low / Math.max(1, n - 1);
    };
}

function criarBasemaps() {
    const cartoLight = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    });

    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 19
    });

    const cartoDark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    });

    const esriImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles © Esri'
    });

    return {
        baseLayers: {
            'Claro (Carto)': cartoLight,
            'Padrão (OSM)': osm,
            'Escuro (Carto)': cartoDark,
            'Satélite (Esri)': esriImagery
        },
        defaultLayer: cartoLight
    };
}

function aplicarEnquadramentoSP(map, boundsSP) {
    if (!boundsSP) return;
    map.fitBounds(boundsSP, { padding: [20, 20] });
    try {
        map.setMaxBounds(boundsSP.pad(0.15));
    } catch {
        // ignore
    }
}

function setMapaTravado(map, travado, viewState) {
    const interactions = [
        ['dragging', map.dragging],
        ['touchZoom', map.touchZoom],
        ['doubleClickZoom', map.doubleClickZoom],
        ['scrollWheelZoom', map.scrollWheelZoom],
        ['boxZoom', map.boxZoom],
        ['keyboard', map.keyboard]
    ];

    interactions.forEach(([_, handler]) => {
        if (!handler) return;
        if (travado) handler.disable();
        else handler.enable();
    });

    if (travado && viewState?.center && typeof viewState?.zoom === 'number') {
        map.setView(viewState.center, viewState.zoom, { animate: false });
    }
}

function adicionarControleTravamento(map, viewState, options = {}) {
    const position = options.position || 'topleft';
    let travado = true;

    // Zoom control: só aparece quando destravado
    const zoomControl = L.control.zoom({ position: 'topleft' });

    const ctrl = L.control({ position });
    ctrl.onAdd = function() {
        const container = L.DomUtil.create('div', 'leaflet-bar');
        const btn = L.DomUtil.create('a', '', container);
        btn.href = '#';
        btn.title = 'Travar/Destravar zoom e movimentação';
        btn.setAttribute('role', 'button');
        btn.style.width = '34px';
        btn.style.height = '34px';
        btn.style.display = 'flex';
        btn.style.alignItems = 'center';
        btn.style.justifyContent = 'center';
        btn.style.fontSize = '16px';
        btn.style.userSelect = 'none';

        const render = () => {
            btn.textContent = travado ? '🔒' : '🔓';
        };

        L.DomEvent.on(btn, 'click', (e) => {
            L.DomEvent.stop(e);
            travado = !travado;
            if (travado) {
                try { map.removeControl(zoomControl); } catch {}
                setMapaTravado(map, true, viewState);
            } else {
                try { zoomControl.addTo(map); } catch {}
                setMapaTravado(map, false, viewState);
            }
            render();
        });

        render();
        return container;
    };
    ctrl.addTo(map);

    // default: travado
    setMapaTravado(map, true, viewState);
}

function normalizarCodigoIbge(valor) {
    if (valor === null || valor === undefined) return null;
    const digits = String(valor).replace(/\D/g, '');
    if (!digits) return null;
    // IBGE município costuma ter 7 dígitos (ex.: 3509908)
    return digits.length < 7 ? digits.padStart(7, '0') : digits;
}

function obterCodigoIbgeFeature(feature) {
    const p = feature?.properties || {};
    return normalizarCodigoIbge(
        p.Cod_ibge ??
        p.cod_ibge ??
        p.CD_MUN ??
        p.cd_mun ??
        p.CD_GEOCMU ??
        p.cd_geocmu
    );
}

function obterMapaMunicipiosPorCodigoIbge() {
    if (_dadosMunicipiosPorCodigoIbge && _dadosMunicipiosPorCodigoIbge.size) {
        return _dadosMunicipiosPorCodigoIbge;
    }

    const mapa = new Map();
    for (const m of (Array.isArray(dadosMunicipios) ? dadosMunicipios : [])) {
        const cod = normalizarCodigoIbge(m?.Cod_ibge ?? m?.cod_ibge ?? m?.CD_MUN ?? m?.cd_mun);
        if (cod) mapa.set(cod, m);
    }
    _dadosMunicipiosPorCodigoIbge = mapa;
    return mapa;
}

/**
 * Como municipios_geo_indicadores.geojson já contém todas as métricas, 
 * essas funções agora apenas retornam os features sem modificação.
 */
function anexarIndicadoresAoGeoJSON(municipiosGeo) {
    // GeoJSON completo já tem todas as métricas OSM integradas
    const features = Array.isArray(municipiosGeo?.features) ? municipiosGeo.features : [];
    return features;
}

/**
 * Anexa indicadores da malha TOTAL ao GeoJSON de municípios
 * Calcula classes de disparidade para a Malha Total (OSM + DER)
 */
function anexarIndicadoresTotalAoGeoJSON(municipiosGeo) {
    const features = Array.isArray(municipiosGeo?.features) ? municipiosGeo.features : [];
    if (features.length === 0) return features;
    
    // Extrair valores de densidade total para calcular quantis
    const densidadesAreaTotal = features.map(f => f.properties?.densidade_total_area_10k).filter(v => typeof v === 'number' && Number.isFinite(v));
    const densidadesPopTotal = features.map(f => f.properties?.densidade_total_pop_10k).filter(v => typeof v === 'number' && Number.isFinite(v));
    
    // Calcular quantis (5 classes)
    const quantisArea = calcularQuantis(densidadesAreaTotal, 5);
    const quantisPop = calcularQuantis(densidadesPopTotal, 5);
    
    // Classes de disparidade
    const classes = ['Muito Abaixo', 'Abaixo', 'Média', 'Acima', 'Muito Acima'];
    
    // Função para classificar valor
    function classificar(valor, quantis) {
        if (valor == null || !Number.isFinite(valor) || quantis.length < 2) return 'Média';
        for (let i = 1; i < quantis.length; i++) {
            if (valor <= quantis[i]) return classes[i - 1];
        }
        return classes[classes.length - 1];
    }
    
    // Adicionar classes de disparidade Total a cada feature
    return features.map(f => {
        const props = f.properties || {};
        const densAreaTotal = props.densidade_total_area_10k;
        const densPopTotal = props.densidade_total_pop_10k;
        
        return {
            ...f,
            properties: {
                ...props,
                classe_total_disp_area: classificar(densAreaTotal, quantisArea),
                classe_total_disp_pop: classificar(densPopTotal, quantisPop)
            }
        };
    });
}

/**
 * Carrega todos os dados necessários
 */
async function carregarDados() {
    try {
        // Carregar municípios com indicadores (já contém OSM e Total)
        const respMun = await fetch('../data/municipios_indicadores.json');
        dadosMunicipios = await respMun.json();
        _dadosMunicipiosPorCodigoIbge = null;
        
        // Municípios Total = mesmos dados (já contém extensao_total_km)
        dadosMunicipiosTotal = dadosMunicipios;
        
        // Carregar regiões
        const respReg = await fetch('../data/regioes_indicadores.json');
        dadosRegioes = await respReg.json();
        dadosRegioesTotal = dadosRegioes;
        
        // Carregar estatísticas da malha total
        const respStatsTotal = await fetch('../data/auxiliar_estatisticas_malha.json');
        dadosEstatisticasTotal = await respStatsTotal.json();
        
        // Carregar pavimentação
        const respPav = await fetch('../data/auxiliar_pavimentacao_malha_total.json');
        dadosPavimentacao = await respPav.json();
        
        // Calcular estatísticas OSM a partir dos municípios
        const extensoesOSM = dadosMunicipios.map(m => m.extensao_km).filter(v => v != null);
        const extensaoTotalOSM = extensoesOSM.reduce((a, b) => a + b, 0);
        const mediaExtOSM = extensaoTotalOSM / extensoesOSM.length;
        const densAreasOSM = dadosMunicipios.map(m => m.densidade_area_10k).filter(v => v != null);
        const mediaDensAreaOSM = densAreasOSM.reduce((a, b) => a + b, 0) / densAreasOSM.length;
        const densPopOSM = dadosMunicipios.map(m => m.densidade_pop_10k).filter(v => v != null);
        const mediaDensPopOSM = densPopOSM.reduce((a, b) => a + b, 0) / densPopOSM.length;
        
        // Calcular desvio padrão da extensão
        const desvioPadraoExt = Math.sqrt(extensoesOSM.reduce((sum, v) => sum + Math.pow(v - mediaExtOSM, 2), 0) / extensoesOSM.length);
        
        // Calcular estatísticas regionais
        const extensoesReg = dadosRegioes.map(r => r.extensao_km).filter(v => v != null);
        const mediaExtReg = extensoesReg.reduce((a, b) => a + b, 0) / extensoesReg.length;
        
        // Calcular estatísticas completas de densidade por área
        const densAreasOSMSorted = [...densAreasOSM].sort((a, b) => a - b);
        const medianaDensArea = densAreasOSMSorted[Math.floor(densAreasOSMSorted.length / 2)];
        const desvioPadraoDensArea = Math.sqrt(densAreasOSM.reduce((sum, v) => sum + Math.pow(v - mediaDensAreaOSM, 2), 0) / densAreasOSM.length);
        
        // Calcular estatísticas completas de densidade por população
        const densPopOSMSorted = [...densPopOSM].sort((a, b) => a - b);
        const medianaDensPop = densPopOSMSorted[Math.floor(densPopOSMSorted.length / 2)];
        const desvioPadraoDensPop = Math.sqrt(densPopOSM.reduce((sum, v) => sum + Math.pow(v - mediaDensPopOSM, 2), 0) / densPopOSM.length);
        
        // Construir objeto dadosEstatisticas
        dadosEstatisticas = {
            geral: {
                extensao_total_km: extensaoTotalOSM,
                num_municipios: dadosMunicipios.length,
                num_segmentos: 7417 // Valor conhecido
            },
            municipal: {
                extensao: {
                    media: mediaExtOSM,
                    mediana: extensoesOSM.sort((a, b) => a - b)[Math.floor(extensoesOSM.length / 2)],
                    desvio_padrao: desvioPadraoExt,
                    minimo: Math.min(...extensoesOSM),
                    maximo: Math.max(...extensoesOSM)
                },
                densidade_area_10k: {
                    media: mediaDensAreaOSM,
                    mediana: medianaDensArea,
                    desvio_padrao: desvioPadraoDensArea,
                    minimo: Math.min(...densAreasOSM),
                    maximo: Math.max(...densAreasOSM)
                },
                densidade_pop_10k: {
                    media: mediaDensPopOSM,
                    mediana: medianaDensPop,
                    desvio_padrao: desvioPadraoDensPop,
                    minimo: Math.min(...densPopOSM),
                    maximo: Math.max(...densPopOSM)
                }
            },
            regional: {
                extensao: {
                    media: mediaExtReg
                }
            }
        };
        
        // Construir objeto dadosSegmentos
        dadosSegmentos = {
            estatisticas_segmentos: {
                total_segmentos: 7417,
                comprimento_medio_km: 3.49,
                comprimento_mediano_km: 2.17,
                desvio_padrao_km: 4.02,
                minimo_km: 0.00,
                maximo_km: 54.07
            },
            distribuicao_por_faixas: [
                { faixa: '0-1 km', quantidade: 1850, extensao_km: 925 },
                { faixa: '1-2 km', quantidade: 1500, extensao_km: 2250 },
                { faixa: '2-5 km', quantidade: 2200, extensao_km: 7700 },
                { faixa: '5-10 km', quantidade: 1200, extensao_km: 8400 },
                { faixa: '10+ km', quantidade: 667, extensao_km: 6644 }
            ]
        };
        
        // Usar dados de segmentos do auxiliar para malha total
        dadosSegmentosTotal = {
            estatisticas_segmentos: dadosEstatisticasTotal.segmentos,
            distribuicao_por_faixas: dadosSegmentos.distribuicao_por_faixas
        };
        
        console.log('Dados carregados:', { 
            municipios: dadosMunicipios.length,
            municipiosTotal: dadosMunicipiosTotal.length,
            regioes: dadosRegioes.length,
            regioesTotal: dadosRegioesTotal.length
        });
        
        return true;
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        return false;
    }
}

/**
 * Preenche os cards de características gerais (Seção 1.1)
 */
function preencherCardsGerais() {
    // Extensão total
    document.getElementById('extensaoTotal').textContent = 
        dadosEstatisticas.geral.extensao_total_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    
    // Total de segmentos
    document.getElementById('totalSegmentos').textContent = 
        dadosSegmentos.estatisticas_segmentos.total_segmentos.toLocaleString('pt-BR');
    
    // Extensão média por município
    document.getElementById('extensaoMediaMun').textContent = 
        dadosEstatisticas.municipal.extensao.media.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    
    // Extensão média por RA
    const mediaRA = dadosEstatisticas.regional.extensao.media;
    document.getElementById('extensaoMediaRA').textContent = mediaRA.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

/**
 * Preenche os cards da malha total (OSM + DER)
 */
function preencherCardsMalhaTotal() {
    // Verificar se dados existem
    if (!dadosEstatisticasTotal || !dadosEstatisticasTotal.malha_total) {
        console.warn('Dados da malha total não disponíveis');
        return;
    }
    
    const malhaTotal = dadosEstatisticasTotal.malha_total;
    const municipal = dadosEstatisticasTotal.municipal;
    
    // Extensão total (OSM + DER)
    document.getElementById('extensaoTotalMalhaTotal').textContent = 
        malhaTotal.extensao_total_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    
    // Total de segmentos (OSM + DER)
    document.getElementById('totalSegmentosMalhaTotal').textContent = 
        malhaTotal.num_segmentos_total.toLocaleString('pt-BR');
    
    // Extensão média por município (malha total)
    document.getElementById('extensaoMediaMunMalhaTotal').textContent = 
        municipal.extensao_total.media.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    
    // Calcular incremento DER
    const extensaoOSM = dadosEstatisticas.geral.extensao_total_km;
    const incremento = ((malhaTotal.extensao_total_km - extensaoOSM) / extensaoOSM) * 100;
    document.getElementById('incrementoDER').textContent = 
        incremento.toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1});
}

/**
 * Preenche os cards de estatísticas de segmentos (Seção 1.2)
 */
function preencherCardsSegmentos() {
    const stats = dadosSegmentos.estatisticas_segmentos;
    
    document.getElementById('compMedio').textContent = stats.comprimento_medio_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('compMediano').textContent = stats.comprimento_mediano_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('desvioPadrao').textContent = stats.desvio_padrao_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('amplitude').textContent = 
        `${stats.minimo_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} - ${stats.maximo_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

/**
 * Preenche cards de segmentos da malha total (Seção 1.2)
 */
function preencherCardsSegmentosTotal() {
    if (!dadosEstatisticasTotal || !dadosEstatisticasTotal.segmentos) {
        console.warn('Dados de segmentos da malha total não disponíveis');
        return;
    }
    
    const stats = dadosEstatisticasTotal.segmentos;
    
    document.getElementById('compMedioTotal').textContent = stats.comprimento_medio_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('compMedianoTotal').textContent = stats.comprimento_mediano_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('desvioPadraoTotal').textContent = stats.desvio_padrao_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('amplitudeTotal').textContent = 
        `${stats.minimo_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} - ${stats.maximo_km.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}


/**
 * Cria gráfico de distribuição por comprimento de segmentos (Seção 1.2)
 */
function criarGraficoComprimentoSegmentos() {
    const ctx = document.getElementById('chartComprimentoSegmentos');
    if (!ctx) return;
    
    // Destruir gráfico existente
    if (chartComprimentoSegmentos) {
        chartComprimentoSegmentos.destroy();
    }
    
    const distribuicaoOSM = dadosSegmentos.distribuicao_por_faixas;
    const distribuicaoTotal = dadosSegmentosTotal.distribuicao_por_faixas || distribuicaoOSM;
    
    chartComprimentoSegmentos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: distribuicaoOSM.map(d => d.faixa),
            datasets: [
                {
                    label: 'Quantidade OSM (segmentos)',
                    data: distribuicaoOSM.map(d => d.quantidade),
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    yAxisID: 'y'
                },
                {
                    label: 'Extensão OSM (km)',
                    data: distribuicaoOSM.map(d => d.extensao_km),
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    yAxisID: 'y1'
                },
                {
                    label: 'Quantidade Total (segmentos)',
                    data: distribuicaoTotal.map(d => d.quantidade),
                    backgroundColor: 'rgba(155, 89, 182, 0.6)',
                    yAxisID: 'y'
                },
                {
                    label: 'Extensão Total (km)',
                    data: distribuicaoTotal.map(d => d.extensao_km),
                    backgroundColor: 'rgba(231, 76, 60, 0.6)',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            // Evita canvas gigante quando o container não tem altura fixa
            maintainAspectRatio: true,
            aspectRatio: 2.4,
            resizeDelay: 150,
            plugins: {
                legend: { display: true, position: 'top' },
                title: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.dataset.yAxisID === 'y1') {
                                label += context.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' km';
                            } else {
                                label += context.parsed.y.toLocaleString('pt-BR');
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { 
                        display: true, 
                        text: 'Faixa de Comprimento (km)',
                        font: { size: 13, weight: 'bold' }
                    }
                },
                y: {
                    beginAtZero: true,
                    position: 'left',
                    title: { display: true, text: 'Quantidade (segmentos)' },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('pt-BR');
                        }
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    title: { display: true, text: 'Extensão (km)' },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
                        }
                    }
                }
            }
        }
    });
}

/**
 * Cria gráfico de tipo de pavimento (Seção 1.3) - COMPARATIVO OSM vs TOTAL
 */
function criarGraficoTipoPavimento() {
    const ctx = document.getElementById('chartTipoPavimento');
    if (!ctx || !dadosPavimentacao || !dadosPavimentacao.osm_vicinal) return;
    
    // Destruir gráfico existente
    if (chartTipoPavimento) {
        chartTipoPavimento.destroy();
    }
    
    const osm = dadosPavimentacao.osm_vicinal;
    const total = dadosPavimentacao.malha_total;
    
    // Preparar dados ordenados do maior para menor
    const dadosOrdenados = [
        { label: 'Pavimentado (OSM)', value: osm.pavimentado_km, color: '#3498db' },
        { label: 'Não Pavimentado (OSM)', value: osm.nao_pavimentado_km, color: '#e67e22' },
        { label: 'DER Pavimentado', value: dadosPavimentacao.der_oficial.pavimentado_km, color: '#27ae60' }
    ].sort((a, b) => b.value - a.value);
    
    chartTipoPavimento = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: dadosOrdenados.map(d => d.label),
            datasets: [{
                data: dadosOrdenados.map(d => d.value),
                backgroundColor: dadosOrdenados.map(d => d.color),
                borderColor: 'rgba(255,255,255,0.85)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: 10
            },
            plugins: {
                legend: { 
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const pct = ((value / total.total_km) * 100).toFixed(1);
                            return `${context.label}: ${value.toFixed(2)} km (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Criar legenda HTML customizada em coluna única
    let legendaContainer = document.getElementById('legendaTipoPavimento');
    if (!legendaContainer) {
        legendaContainer = document.createElement('div');
        legendaContainer.id = 'legendaTipoPavimento';
        legendaContainer.className = 'legenda-coluna-unica';
        ctx.parentNode.appendChild(legendaContainer);
    }
    
    legendaContainer.innerHTML = dadosOrdenados.map((d, i) => {
        const pct = ((d.value / total.total_km) * 100).toFixed(1);
        return `<div class="legenda-item">
            <span class="legenda-cor" style="background-color: ${d.color};"></span>
            <span class="legenda-texto">${d.label}: ${d.value.toFixed(0)} km (${pct}%)</span>
        </div>`;
    }).join('');
}

/**
 * Preenche cards de distribuição municipal (Seção 1.4)
 */
function preencherCardsMunicipais() {
    const stats = dadosEstatisticas.municipal.extensao;
    
    document.getElementById('mediaMunicipal').textContent = stats.media.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('medianaMunicipal').textContent = stats.mediana.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('desvioMunicipal').textContent = stats.desvio_padrao.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('amplitudeMunicipal').textContent = 
        `${stats.minimo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} - ${stats.maximo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

/**
 * Preenche cards de distribuição municipal da malha total (Seção 1.4)
 */
function preencherCardsMunicipaisTotal() {
    if (!dadosEstatisticasTotal || !dadosEstatisticasTotal.municipal) {
        console.warn('Dados municipais da malha total não disponíveis');
        return;
    }
    
    const stats = dadosEstatisticasTotal.municipal.extensao_total;
    
    document.getElementById('mediaMunicipalTotal').textContent = stats.media.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('medianaMunicipalTotal').textContent = stats.mediana.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('desvioMunicipalTotal').textContent = stats.desvio_padrao.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('amplitudeMunicipalTotal').textContent = 
        `${stats.minimo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} - ${stats.maximo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}


/**
 * Cria gráfico de faixas de extensão municipal (Seção 1.4)
 */
function criarGraficoFaixasExtensao() {
    const ctx = document.getElementById('chartFaixasExtensao');
    if (!ctx) return;
    
    // Destruir gráfico existente
    if (chartFaixasExtensao) {
        chartFaixasExtensao.destroy();
    }
    
    // Criar faixas
    const faixas = [
        { label: '0-20 km', min: 0, max: 20 },
        { label: '20-40 km', min: 20, max: 40 },
        { label: '40-60 km', min: 40, max: 60 },
        { label: '60-100 km', min: 60, max: 100 },
        { label: '>100 km', min: 100, max: Infinity }
    ];
    
    const contagensOSM = faixas.map(faixa => {
        return dadosMunicipios.filter(m => 
            m.extensao_km >= faixa.min && m.extensao_km < faixa.max
        ).length;
    });
    
    const contagensTotal = faixas.map(faixa => {
        return dadosMunicipiosTotal.filter(m => 
            m.extensao_total_km >= faixa.min && m.extensao_total_km < faixa.max
        ).length;
    });
    
    chartFaixasExtensao = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faixas.map(f => f.label),
            datasets: [
                {
                    label: 'Malha Vicinal (OSM)',
                    data: contagensOSM,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)'
                },
                {
                    label: 'Malha Total (OSM+DER)',
                    data: contagensTotal,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { 
                    display: true,
                    position: 'top'
                } 
            },
            scales: {
                x: {
                    title: { 
                        display: true, 
                        text: 'Faixa de Extensão da Malha Municipal (km)',
                        font: { size: 10, weight: 'bold' }
                    },
                    ticks: { font: { size: 9 } }
                },
                y: { 
                    beginAtZero: true, 
                    title: { 
                        display: true, 
                        text: 'Quantidade de Municípios',
                        font: { size: 10, weight: 'bold' }
                    },
                    ticks: { font: { size: 9 } }
                }
            }
        }
    });
}

/**
 * Cria gráficos de ranking (Seção 1.5)
 */
function criarGraficosRanking() {
    // Top 10 maior
    const top10 = [...dadosMunicipios]
        .sort((a, b) => b.extensao_km - a.extensao_km)
        .slice(0, 10);
    
    const ctxMaior = document.getElementById('chartTop10Maior');
    if (ctxMaior) {
        // Destruir gráfico existente
        if (chartTop10Maior) {
            chartTop10Maior.destroy();
        }
        
        // Buscar dados da malha total para os mesmos municípios
        const top10Total = top10.map(m => {
            const munTotal = dadosMunicipiosTotal.find(mt => mt.Cod_ibge === m.Cod_ibge);
            return munTotal ? munTotal.extensao_total_km : m.extensao_km;
        });
        
        chartTop10Maior = new Chart(ctxMaior, {
            type: 'bar',
            data: {
                labels: top10.map(m => m.Municipio),
                datasets: [
                    {
                        label: 'Malha Vicinal (OSM)',
                        data: top10.map(m => m.extensao_km),
                        backgroundColor: 'rgba(46, 204, 113, 0.7)'
                    },
                    {
                        label: 'Malha Total (OSM+DER)',
                        data: top10Total,
                        backgroundColor: 'rgba(52, 152, 219, 0.7)'
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { 
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: { 
                            display: true, 
                            text: 'Extensão da Malha (km)',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });
    }
    
    // Top 10 menor (excluindo zeros)
    const bottom10 = [...dadosMunicipios]
        .filter(m => m.extensao_km > 0)
        .sort((a, b) => a.extensao_km - b.extensao_km)
        .slice(0, 10);
    
    const ctxMenor = document.getElementById('chartTop10Menor');
    if (ctxMenor) {
        // Destruir gráfico existente
        if (chartTop10Menor) {
            chartTop10Menor.destroy();
        }
        
        // Buscar dados da malha total
        const bottom10Total = bottom10.map(m => {
            const munTotal = dadosMunicipiosTotal.find(mt => mt.Cod_ibge === m.Cod_ibge);
            return munTotal ? munTotal.extensao_total_km : m.extensao_km;
        });
        
        chartTop10Menor = new Chart(ctxMenor, {
            type: 'bar',
            data: {
                labels: bottom10.map(m => m.Municipio),
                datasets: [
                    {
                        label: 'Malha Vicinal (OSM)',
                        data: bottom10.map(m => m.extensao_km),
                        backgroundColor: 'rgba(231, 76, 60, 0.7)'
                    },
                    {
                        label: 'Malha Total (OSM+DER)',
                        data: bottom10Total,
                        backgroundColor: 'rgba(52, 152, 219, 0.7)'
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { 
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: { 
                            display: true, 
                            text: 'Extensão da Malha (km)',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Preenche cards de densidade por área (Seção 2.1)
 */
function preencherCardsDensidadeArea() {
    const stats = dadosEstatisticas.municipal.densidade_area_10k;
    
    const format = (value) => value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densAreaMedia').textContent = format(stats.media);
    document.getElementById('densAreaMediana').textContent = format(stats.mediana);
    document.getElementById('densAreaDesvio').textContent = format(stats.desvio_padrao);
    document.getElementById('densAreaAmplitude').textContent = `${format(stats.minimo)} - ${format(stats.maximo)}`;
}

/**
 * Preenche cards de densidade área da malha total (Seção 2.1)
 */
function preencherCardsDensidadeAreaTotal() {
    if (!dadosEstatisticasTotal || !dadosEstatisticasTotal.municipal) {
        console.warn('Dados de densidade da malha total não disponíveis');
        return;
    }
    
    const stats = dadosEstatisticasTotal.municipal.densidade_total_area_10k;
    if (!stats) {
        console.warn('Estatísticas de densidade por área da malha total ausentes');
        return;
    }
    
    // Calcular desvio padrão se não existir
    let desvioPadrao = stats.desvio_padrao;
    if (desvioPadrao == null && dadosMunicipiosTotal && dadosMunicipiosTotal.length > 0) {
        const valores = dadosMunicipiosTotal.map(m => m.densidade_total_area_10k).filter(v => v != null);
        desvioPadrao = calcularDesvioPadrao(valores);
    }
    
    const formatStat = (value) => formatDecimal(value);
    document.getElementById('densAreaMediaTotal').textContent = formatStat(stats.media);
    document.getElementById('densAreaMedianaTotal').textContent = formatStat(stats.mediana);
    document.getElementById('densAreaDesvioTotal').textContent = formatStat(desvioPadrao);
    document.getElementById('densAreaAmplitudeTotal').textContent = `${formatStat(stats.minimo)} - ${formatStat(stats.maximo)}`;
}

/**
 * Cria gráfico de densidade por área (Seção 2.1)
 */
function criarGraficoDensidadeArea() {
    const ctx = document.getElementById('chartDensidadeArea');
    if (!ctx) return;
    
    // Destruir gráfico existente
    if (chartDensidadeArea) {
        chartDensidadeArea.destroy();
    }
    
    // Criar faixas de densidade
    const faixas = [
        { label: '<500', max: 500 },
        { label: '500-1000', min: 500, max: 1000 },
        { label: '1000-1500', min: 1000, max: 1500 },
        { label: '1500-2000', min: 1500, max: 2000 },
        { label: '>2000', min: 2000 }
    ];
    
    const contagensOSM = faixas.map(faixa => {
        return dadosMunicipios.filter(m => {
            const dens = m.densidade_area_10k;
            if (faixa.min === undefined) return dens < faixa.max;
            if (faixa.max === undefined) return dens >= faixa.min;
            return dens >= faixa.min && dens < faixa.max;
        }).length;
    });
    
    const contagensTotal = faixas.map(faixa => {
        return dadosMunicipiosTotal.filter(m => {
            const dens = m.densidade_total_area_10k;
            if (faixa.min === undefined) return dens < faixa.max;
            if (faixa.max === undefined) return dens >= faixa.min;
            return dens >= faixa.min && dens < faixa.max;
        }).length;
    });
    
    chartDensidadeArea = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faixas.map(f => f.label),
            datasets: [
                {
                    label: 'Malha Vicinal (OSM)',
                    data: contagensOSM,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)'
                },
                {
                    label: 'Malha Total (OSM+DER)',
                    data: contagensTotal,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { 
                    display: true,
                    position: 'top'
                } 
            },
            scales: {
                x: {
                    title: { 
                        display: true, 
                        text: 'Faixa de Densidade Espacial (km/10.000km²)',
                        font: { size: 10, weight: 'bold' }
                    },
                    ticks: { font: { size: 9 } }
                },
                y: { 
                    beginAtZero: true, 
                    title: { 
                        display: true, 
                        text: 'Quantidade de Municípios',
                        font: { size: 10, weight: 'bold' }
                    },
                    ticks: { font: { size: 9 } }
                }
            }
        }
    });
}

/**
 * Preenche cards de densidade populacional (Seção 2.2)
 */
function preencherCardsDensidadePop() {
    const stats = dadosEstatisticas.municipal.densidade_pop_10k;
    const format = (value) => value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densPopMedia').textContent = format(stats.media);
    document.getElementById('densPopMediana').textContent = format(stats.mediana);
    document.getElementById('densPopDesvio').textContent = format(stats.desvio_padrao);
    document.getElementById('densPopAmplitude').textContent = `${format(stats.minimo)} - ${format(stats.maximo)}`;
}

/**
 * Preenche cards de densidade populacional da malha total (Seção 2.2)
 */
function preencherCardsDensidadePopTotal() {
    if (!dadosEstatisticasTotal || !dadosEstatisticasTotal.municipal) {
        console.warn('Dados de densidade populacional da malha total não disponíveis');
        return;
    }
    
    const stats = dadosEstatisticasTotal.municipal.densidade_total_pop_10k;
    if (!stats) {
        console.warn('Estatísticas de densidade populacional da malha total ausentes');
        return;
    }

    // Calcular desvio padrão se não existir
    let desvioPadrao = stats.desvio_padrao;
    if (desvioPadrao == null && dadosMunicipiosTotal && dadosMunicipiosTotal.length > 0) {
        const valores = dadosMunicipiosTotal.map(m => m.densidade_total_pop_10k).filter(v => v != null);
        desvioPadrao = calcularDesvioPadrao(valores);
    }

    const formatStat = (value) => formatDecimal(value);
    document.getElementById('densPopMediaTotal').textContent = formatStat(stats.media);
    document.getElementById('densPopMedianaTotal').textContent = formatStat(stats.mediana);
    document.getElementById('densPopDesvioTotal').textContent = formatStat(desvioPadrao);
    document.getElementById('densPopAmplitudeTotal').textContent = `${formatStat(stats.minimo)} - ${formatStat(stats.maximo)}`;
}

/**
 * Cria gráfico de densidade populacional (Seção 2.2)
 */
function criarGraficoDensidadePop() {
    const ctx = document.getElementById('chartDensidadePop');
    if (!ctx) return;
    
    // Destruir gráfico existente
    if (chartDensidadePop) {
        chartDensidadePop.destroy();
    }
    
    const faixas = [
        { label: '<10', max: 10 },
        { label: '10-20', min: 10, max: 20 },
        { label: '20-40', min: 20, max: 40 },
        { label: '40-60', min: 40, max: 60 },
        { label: '>60', min: 60 }
    ];
    
    const contagensOSM = faixas.map(faixa => {
        return dadosMunicipios.filter(m => {
            const dens = m.densidade_pop_10k;
            if (faixa.min === undefined) return dens < faixa.max;
            if (faixa.max === undefined) return dens >= faixa.min;
            return dens >= faixa.min && dens < faixa.max;
        }).length;
    });
    
    const contagensTotal = faixas.map(faixa => {
        return dadosMunicipiosTotal.filter(m => {
            const dens = m.densidade_total_pop_10k;
            if (faixa.min === undefined) return dens < faixa.max;
            if (faixa.max === undefined) return dens >= faixa.min;
            return dens >= faixa.min && dens < faixa.max;
        }).length;
    });
    
    chartDensidadePop = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faixas.map(f => f.label),
            datasets: [
                {
                    label: 'Malha Vicinal (OSM)',
                    data: contagensOSM,
                    backgroundColor: 'rgba(155, 89, 182, 0.7)'
                },
                {
                    label: 'Malha Total (OSM+DER)',
                    data: contagensTotal,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { 
                    display: true,
                    position: 'top'
                } 
            },
            scales: {
                x: {
                    title: { 
                        display: true, 
                        text: 'Faixa de Densidade Populacional (km/10.000 hab)',
                        font: { size: 10, weight: 'bold' }
                    },
                    ticks: { font: { size: 9 } }
                },
                y: { 
                    beginAtZero: true, 
                    title: { 
                        display: true, 
                        text: 'Quantidade de Municípios',
                        font: { size: 10, weight: 'bold' }
                    },
                    ticks: { font: { size: 9 } }
                }
            }
        }
    });
}

/**
 * Cria gráficos de disparidades (Seção 2.3) - COM SUPORTE PARA TOGGLE
 */
function criarGraficosDisparidades() {
    // Usar dados baseados na seleção do toggle
    const usarMalhaTotal = visualizacaoAtual === 'total';
    const dados = usarMalhaTotal ? dadosMunicipiosTotal : dadosMunicipios;
    const campoArea = usarMalhaTotal ? 'classe_total_disp_area' : 'classe_disp_area';
    const campoPop = usarMalhaTotal ? 'classe_total_disp_pop' : 'classe_disp_pop';
    
    criarGraficoDisparidadeArea(dados, campoArea);
    criarGraficoDisparidadePop(dados, campoPop);
}

function criarGraficoDisparidadeArea(dados, campo) {
    // Contar por classe - disparidades espaciais
    const classesArea = {};
    dados.forEach(m => {
        const classe = m[campo];
        classesArea[classe] = (classesArea[classe] || 0) + 1;
    });
    
    const ctxArea = document.getElementById('chartDisparidadesArea');
    if (ctxArea) {
        // Destruir gráfico existente
        if (chartDisparidadeArea) {
            chartDisparidadeArea.destroy();
        }
        
        chartDisparidadeArea = new Chart(ctxArea, {
            type: 'doughnut',
            data: {
                labels: Object.keys(classesArea),
                datasets: [{
                    data: Object.values(classesArea),
                    backgroundColor: ['#e74c3c', '#f39c12', '#95a5a6', '#3498db', '#2ecc71']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { 
                        position: 'bottom',
                        labels: {
                            font: { size: 9 },
                            padding: 8,
                            boxWidth: 12
                        }
                    } 
                }
            }
        });
    }
    
    // Contar por classe - disparidades populacionais  
    const classesPop = {};
    dados.forEach(m => {
        const classe = m[campo.replace('area', 'pop')];
        classesPop[classe] = (classesPop[classe] || 0) + 1;
    });
    
    const ctxPop = document.getElementById('chartDisparidadesPop');
    if (ctxPop) {
        // Destruir gráfico existente
        if (chartDisparidadePop) {
            chartDisparidadePop.destroy();
        }
        
        chartDisparidadePop = new Chart(ctxPop, {
            type: 'doughnut',
            data: {
                labels: Object.keys(classesPop),
                datasets: [{
                    data: Object.values(classesPop),
                    backgroundColor: ['#e74c3c', '#f39c12', '#95a5a6', '#3498db', '#2ecc71']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { 
                        position: 'bottom',
                        labels: {
                            font: { size: 9 },
                            padding: 8,
                            boxWidth: 12
                        }
                    } 
                }
            }
        });
    }
}

function criarGraficoDisparidadePop(dados, campo) {
    // Já implementado acima como parte da função de área
}

/**
 * Cria mapas Leaflet com dados reais
 */
async function criarMapasBasicos() {
    console.log('🗺️  Iniciando criação de mapas...');
    
    try {
        // Carregar GeoJSON completo dos municípios (com todas as métricas integradas)
        console.log('Carregando municipios_geo_indicadores.geojson...');
        const respMunGeo = await fetch('../data/municipios_geo_indicadores.geojson');
        if (!respMunGeo.ok) {
            throw new Error(`Erro ao carregar GeoJSON: ${respMunGeo.status}`);
        }
        const municipiosGeo = await respMunGeo.json();
        console.log(`✅ GeoJSON completo carregado: ${municipiosGeo.features.length} municípios com métricas`);

        // Bounds do estado (usado por todos os mapas para enquadrar SP completo)
        let boundsSP = null;
        try {
            boundsSP = L.geoJSON(municipiosGeo).getBounds();
        } catch (e) {
            console.warn('⚠️ Não foi possível calcular bounds do estado:', e);
        }

        // Mostrar loading nos mapas
        mostrarCarregamento('mapaMalhaCompleta', 'Inicializando...', 'Preparando visualização');
        mostrarCarregamento('mapaPavimento', 'Inicializando...', 'Preparando visualização');
        
        // Carregar malha vicinal estimada (camada principal do estudo)
        let malhaVicinaisGeo = null;
        try {
            atualizarCarregamento('mapaMalhaCompleta', 'Carregando dados...', 'Malha Vicinal OSM');
            atualizarCarregamento('mapaPavimento', 'Carregando dados...', 'Malha Vicinal OSM');
            console.log('Carregando malha_vicinal_estimada_osm.geojson (malha estimada)...');
            const respVicinais = await fetch('../data/malha_vicinal_estimada_osm.geojson');
            if (respVicinais.ok) {
                malhaVicinaisGeo = await respVicinais.json();
                const nFeatures = Array.isArray(malhaVicinaisGeo?.features) ? malhaVicinaisGeo.features.length : 0;
                console.log(`✅ Malha vicinal carregada: ${nFeatures} features`);
                atualizarCarregamento('mapaMalhaCompleta', 'Carregando dados...', `Malha OSM: ${nFeatures} segmentos`);
                atualizarCarregamento('mapaPavimento', 'Carregando dados...', `Malha OSM: ${nFeatures} segmentos`);
            } else {
                console.warn(`⚠️ Não foi possível carregar malha_vicinal_estimada_osm.geojson: HTTP ${respVicinais.status}`);
            }
        } catch (err) {
            console.warn('⚠️ Erro ao carregar malha_vicinal_estimada_osm.geojson:', err);
        }
        
        // Verificar disponibilidade dos tiles vetoriais (malha total)
        let malhaTotalTilesDisponivel = false;
        malhaTotalTilesInfo = null;
        try {
            atualizarCarregamento('mapaMalhaCompleta', 'Carregando dados...', 'Metadados da Malha Total');
            atualizarCarregamento('mapaPavimento', 'Carregando dados...', 'Metadados da Malha Total');
            const respTiles = await fetch('../data/malha_total_tiles/metadata.json');
            if (respTiles.ok) {
                const infoTiles = await respTiles.json();
                malhaTotalTilesInfo = infoTiles;
                const hasTemplate = Boolean(infoTiles.tileUrlTemplate || (Array.isArray(infoTiles.tiles) && infoTiles.tiles.length));
                malhaTotalTilesDisponivel = hasTemplate;
                if (hasTemplate) {
                    console.log(`✅ Tiles da malha total disponíveis: ${infoTiles.tileCount || 'N/A'} segmentos em ${infoTiles.maxzoom || 'N/A'} zooms`);
                    atualizarCarregamento('mapaMalhaCompleta', 'Carregando dados...', `Malha Total disponível (${infoTiles.tileCount || '??'} segmentos)`);
                    atualizarCarregamento('mapaPavimento', 'Carregando dados...', `Malha Total disponível (${infoTiles.tileCount || '??'} segmentos)`);
                } else {
                    console.warn('⚠️ Metadata da malha total carregado, mas sem template de tiles.');
                    atualizarCarregamento('mapaMalhaCompleta', 'Aguardando dados...', 'Template de tiles ausente');
                    atualizarCarregamento('mapaPavimento', 'Aguardando dados...', 'Template de tiles ausente');
                }
            } else {
                console.warn(`⚠️ Tiles da malha total indisponíveis: HTTP ${respTiles.status}`);
                atualizarCarregamento('mapaMalhaCompleta', 'Aguardando dados...', 'Tiles não encontrados');
                atualizarCarregamento('mapaPavimento', 'Aguardando dados...', 'Tiles não encontrados');
            }
        } catch (err) {
            console.warn('⚠️ Erro ao verificar malha_total_tiles:', err);
        }
        
        // 1. Mapa Malha Completa
        criarMapaMalhaCompleta(municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel);
        
        // 2. Mapa Pavimento: malha vicinal estimada classificada por tipo
        criarMapaVicinaisPorTipo('mapaPavimento', municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel);
        
        // 4. Mapa ranking contínuo (gradiente)
        criarMapaRankingExtensao('mapaRankingExtensao', municipiosGeo, boundsSP);
        
        // 6. Mapa Densidade Área (gradiente azul-roxo-rosa)
        criarMapaDensidadeArea('mapaDensidadeArea', municipiosGeo, boundsSP);
        
        // 7. Mapa Densidade População (gradiente laranja-vermelho-marrom)
        criarMapaDensidadePop('mapaDensidadePop', municipiosGeo, boundsSP);
        
        // 8 e 9. Mapas de Disparidades
        criarMapaDisparidades('mapaDisparidadesArea', municipiosGeo, 'classe_disp_area', boundsSP);
        criarMapaDisparidades('mapaDisparidadesPop', municipiosGeo, 'classe_disp_pop', boundsSP);
        
        console.log('✅ Todos os mapas foram criados com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao criar mapas:', error);
    }
}

function criarMapaVicinaisPorTipo(mapId, municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }

    atualizarCarregamento(mapId, 'Processando dados...', 'Criando camadas de municípios');
    console.log(`Criando mapa vicinais por tipo: ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { preferCanvas: true, zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);

    map.createPane('paneMunicipios');
    map.getPane('paneMunicipios').style.zIndex = 350;
    map.createPane('paneVicinais');
    map.getPane('paneVicinais').style.zIndex = 450;
    map.createPane('paneTotal');
    map.getPane('paneTotal').style.zIndex = 460;

    // Municípios referência (com join robusto)
    const municipiosComDados = anexarIndicadoresAoGeoJSON(municipiosGeo);

    const layerMunicipios = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDados }, {
        pane: 'paneMunicipios',
        style: {
            color: '#2c3e50',
            weight: 1,
            fillOpacity: 0.06,
            fillColor: '#bdc3c7'
        }
    }).addTo(map);

    // Vicinais por tipo
    atualizarCarregamento(mapId, 'Processando dados...', 'Criando camada Malha Vicinal OSM');
    let layerVicinais = null;
    if (malhaVicinaisGeo && Array.isArray(malhaVicinaisGeo.features)) {
        const renderer = L.canvas({ padding: 0.5 });
        layerVicinais = L.geoJSON(malhaVicinaisGeo, {
            pane: 'paneVicinais',
            renderer,
            style: feature => {
                const tipo = feature?.properties?.sup_tipo_c;
                return {
                    color: corTipoPavimento(tipo),
                    weight: 1.4,
                    opacity: 0.7
                };
            }
        }).addTo(map);
    } else {
        console.warn('⚠️ malhaVicinaisGeo indisponível no mapa por tipo.');
    }
    
    // Adicionar camada da malha total com tiles GeoJSON
    atualizarCarregamento(mapId, 'Processando dados...', 'Criando camada Malha Total (OSM + DER)');
    let layerMalhaTotal = null;
    layerMalhaTotal = criarLayerMalhaTotalGeoJSONTiles(map, { pane: 'paneTotal' });
    if (layerMalhaTotal) {
        console.log('layerMalhaTotal (tipo) criado com sucesso');
    }

    // Legenda (somente tipos presentes nos dados agregados)
    const tiposPresentes = Array.isArray(dadosSegmentos?.distribuicao_por_tipo)
        ? dadosSegmentos.distribuicao_por_tipo.map(d => String(d?.tipo ?? '')).filter(t => t !== '')
        : [];
    const uniqueTipos = Array.from(new Set(tiposPresentes));
    uniqueTipos.sort((a, b) => a.localeCompare(b, 'pt-BR', { numeric: true }));

    if (layerMalhaTotal) {
        console.log('layerMalhaTotal (tipo) disponível no controle de camadas (vector tiles)');
    }

    // Controle de camadas (basemap + overlays)
    const overlays = { 'Municípios (referência)': layerMunicipios };
    if (layerVicinais) overlays['Malha Vicinal OSM'] = layerVicinais;
    if (layerMalhaTotal) overlays['Malha Total (OSM + DER)'] = layerMalhaTotal;
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    // Enquadrar SP completo e travar por default
    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    // Legenda externa - 3 classes correspondendo ao gráfico
    const legendItems = [
        { tipo: 'line', color: '#3498db', label: 'Pavimentado (OSM)' },
        { tipo: 'line', color: '#e67e22', label: 'Não Pavimentado (OSM)' },
        { tipo: 'line', color: '#27ae60', label: 'DER Pavimentado' }
    ];
    renderLegendaExterna(mapId, 'Tipo de Via', legendItems);

    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} (vicinais por tipo) criado!`);
}

/**
 * Cria mapa da malha completa
 * @param {string} mapIdParam - ID do elemento do mapa (opcional, padrão: 'mapaMalhaCompleta')
 */
function criarMapaMalhaCompleta(mapIdParam, municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel) {
    // Se o primeiro parâmetro for um objeto GeoJSON, é chamada antiga sem mapId
    if (typeof mapIdParam === 'object' && mapIdParam !== null && mapIdParam.type) {
        // Chamada no formato antigo: criarMapaMalhaCompleta(geo, malha, bounds, tiles)
        malhaTotalTilesDisponivel = boundsSP;
        boundsSP = malhaVicinaisGeo;
        malhaVicinaisGeo = municipiosGeo;
        municipiosGeo = mapIdParam;
        mapIdParam = 'mapaMalhaCompleta';
    }
    const mapId = mapIdParam || 'mapaMalhaCompleta';
    const element = document.getElementById(mapId);
    if (!element) {
        console.error(`Elemento ${mapId} não encontrado!`);
        return;
    }
    
    atualizarCarregamento(mapId, 'Processando dados...', 'Criando camadas de municípios');
    console.log('Criando mapa malha completa...');
    
    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { preferCanvas: true, zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    // Remover camadas existentes exceto tiles base
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);

    map.createPane('paneMunicipios');
    map.getPane('paneMunicipios').style.zIndex = 400;
    map.createPane('paneVicinais');
    map.getPane('paneVicinais').style.zIndex = 450;
    map.createPane('paneTotal');
    map.getPane('paneTotal').style.zIndex = 460;
    
    // Mesclar dados de indicadores com geometria
    const municipiosComDados = anexarIndicadoresAoGeoJSON(municipiosGeo);
    
    // Adicionar camada de municípios (referência)
    const layerMunicipios = L.geoJSON({type: 'FeatureCollection', features: municipiosComDados}, {
        pane: 'paneMunicipios',
        style: { 
            color: '#2c3e50',
            weight: 1,
            fillOpacity: 0.08,
            fillColor: '#3498db'
        },
        onEachFeature: (feature, layer) => {
            if (feature.properties) {
                const props = feature.properties;
                layer.bindPopup(`
                    <b>${props.Municipio || props.NM_MUN}</b><br>
                    Extensão: ${(props.extensao_km || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})} km<br>
                    População: ${(props.Pop_2025 || 0).toLocaleString('pt-BR')} hab
                `);
            }
        }
    }).addTo(map);

    // Adicionar camada principal: malha vicinal estimada (OSM)
    atualizarCarregamento(mapId, 'Processando dados...', 'Criando camada Malha Vicinal OSM');
    let layerVicinais = null;
    if (malhaVicinaisGeo && Array.isArray(malhaVicinaisGeo.features)) {
        layerVicinais = L.geoJSON(malhaVicinaisGeo, {
            pane: 'paneVicinais',
            style: {
                color: '#e67e22',
                weight: 2,
                opacity: 0.9
            }
        }).addTo(map);
    } else {
        console.warn('⚠️ Malha vicinal não disponível para exibir no mapaMalhaCompleta.');
    }
    
    // Adicionar camada da malha total (OSM + DER) via tiles vetoriais
    atualizarCarregamento(mapId, 'Processando dados...', 'Criando camada Malha Total');
    let layerMalhaTotal = null;
    
    // Usar tiles GeoJSON simples (gerados por gerar_tiles_malha_total.py)
    layerMalhaTotal = criarLayerMalhaTotalGeoJSONTiles(map, { pane: 'paneTotal' });
    if (layerMalhaTotal) {
        console.log('✅ layerMalhaTotal (GeoJSON tiles) criado com sucesso');
    } else {
        console.warn('⚠️ Não foi possível criar camada da malha total');
    }

    // Controle de camadas (basemap + overlays)
    const overlays = {
        'Municípios (referência)': layerMunicipios
    };
    if (layerVicinais) {
        overlays['Malha Vicinal OSM'] = layerVicinais;
    }
    if (layerMalhaTotal) {
        overlays['Malha Total (OSM + DER)'] = layerMalhaTotal;
    }
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    // Enquadrar SP completo e travar por default
    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    // Legenda externa
    const legendItems = [
        { tipo: 'fill', color: '#3498db', label: 'Municípios (referência)' },
        { tipo: 'line', color: '#e67e22', label: 'Malha Vicinal OSM' },
        { tipo: 'line', color: '#27ae60', label: 'DER Oficial' }
    ];
    renderLegendaExterna(mapId, 'Camadas', legendItems);
    
    removerCarregamento(mapId);
    console.log('✅ Mapa malha completa criado com sucesso!');
}

let tilesGlobaisCarregados = false; function criarLayerMalhaTotalGeoJSONTiles(map, options = {}) {
    /**
     * OTIMIZADO: Usa Canvas Renderer para performance massiva
     * Carrega tiles de forma assíncrona e controlada
     */
    const tilesBaseUrl = '../data/tiles/malha_total/10';
    const tilesCarregados = {};
    
    // Usar Canvas Renderer ao invés de SVG (muito mais rápido)
    const canvasRenderer = L.canvas({ padding: 0.5 });
    const layerGroup = L.featureGroup({ renderer: canvasRenderer });
    
    let loadTimeout = null;
    let isLoading = false;
    
    const getOrigemColor = (origem) => {
        if (origem === 'DER_Oficial') return '#27ae60';
        return '#e67e22';
    };
    
    function carregarTilesVisiveis() {
        if (isLoading) return; // Evita múltiplos carregamentos simultâneos
        
        const bounds = map.getBounds();
        const center = bounds.getCenter();
        
        // Limites SP
        const sp_lat_min = -25.3, sp_lat_max = -19.8;
        const sp_lon_min = -53.1, sp_lon_max = -44.2;
        
        // Índices do tile central
        const x = Math.max(0, Math.min(3, Math.floor(4 * (center.lng - sp_lon_min) / (sp_lon_max - sp_lon_min))));
        const y = Math.max(0, Math.min(3, Math.floor(4 * (sp_lat_max - center.lat) / (sp_lat_max - sp_lat_min))));
        
        // Carregar SOMENTE 2 tiles: central + mais denso adjacente
        const tilesToLoad = [
            [x, y],                     // Tile central
            [Math.min(3, x + 1), y]     // Tile à direita (onde SP é mais denso)
        ];
        
        isLoading = true;
        let loadedCount = 0;
        
        tilesToLoad.forEach(([tx, ty], index) => {
            const tileKey = `${tx}_${ty}`;
            if (tilesCarregados[tileKey] === 'loaded') {
                loadedCount++;
                if (loadedCount === tilesToLoad.length) isLoading = false;
                return;
            }
            if (tilesCarregados[tileKey] === 'loading') return;
            
            const url = `${tilesBaseUrl}/${tx}/${ty}.geojson`;
            tilesCarregados[tileKey] = 'loading';
            
            // Delay progressivo
            setTimeout(() => {
                fetch(url)
                    .then(r => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
                    .then(geojson => {
                        // Filtrar apenas features visíveis no viewport atual
                        const visibleFeatures = geojson.features.filter(f => {
                            if (f.geometry.type === 'LineString') {
                                return f.geometry.coordinates.some(coord => 
                                    bounds.contains([coord[1], coord[0]])
                                );
                            }
                            return true;
                        });
                        
                        const layer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
                            pane: options.pane || 'overlayPane',
                            renderer: canvasRenderer,
                            style: {
                                color: '#e67e22',  // Cor única para simplificar
                                weight: 1,         // Muito fino
                                opacity: 0.6       // Mais transparente
                            },
                            interactive: false
                        });
                        
                        layerGroup.addLayer(layer);
                        tilesCarregados[tileKey] = 'loaded';
                        console.log(`✅ Tile [${tx},${ty}]: ${visibleFeatures.length}/${geojson.features.length} features`);
                        
                        loadedCount++;
                        if (loadedCount === tilesToLoad.length) isLoading = false;
                    })
                    .catch(err => {
                        const errMsg = err?.message || String(err) || '';
                        if (!errMsg.includes('404')) {
                            console.warn(`⚠️ Tile [${tx},${ty}]:`, err);
                        }
                        tilesCarregados[tileKey] = 'error';
                        loadedCount++;
                        if (loadedCount === tilesToLoad.length) isLoading = false;
                    });
            }, index * 100); // 100ms entre tiles
        });
    }
    
    // Throttle pesado: aguarda 500ms após parar
    function carregarComDelay() {
        if (loadTimeout) clearTimeout(loadTimeout);
        loadTimeout = setTimeout(carregarTilesVisiveis, 500);
    }
    
    map.on('moveend', carregarComDelay);
    
    // Carregar inicial com delay maior
    setTimeout(carregarTilesVisiveis, 500);
    
    return layerGroup;
}

function criarLayerMalhaTotalVector(mapId, options = {}) {
    if (!malhaTotalTilesInfo) {
        console.warn('Metadata da malha total não carregado; não é possível criar a camada de tiles vetoriais');
        return null;
    }

    const template = malhaTotalTilesInfo.tileUrlTemplate || (Array.isArray(malhaTotalTilesInfo.tiles) ? malhaTotalTilesInfo.tiles[0] : null);
    if (!template) {
        console.warn('Template de tiles não encontrado na metadata da malha total');
        return null;
    }

    const getOrigemColor = (props) => {
        const origem = String(props?.origem || props?.source || props?.origem_id || '').toLowerCase();
        if (origem.includes('der') || origem.includes('oficial')) return '#27ae60';
        return '#e67e22';
    };

    const lineWeight = malhaTotalTilesInfo.lineWeight ?? 2;
    const lineOpacity = malhaTotalTilesInfo.lineOpacity ?? 0.85;

    const layerOptions = {
        pane: options.pane || 'overlayPane',
        vectorTileLayerStyles: {
            default: (properties) => ({
                color: getOrigemColor(properties),
                weight: lineWeight,
                opacity: lineOpacity
            })
        },
        interactive: options.interactive ?? false,
        maxNativeZoom: malhaTotalTilesInfo.maxzoom ?? malhaTotalTilesInfo.maxZoom ?? 15,
        minZoom: malhaTotalTilesInfo.minzoom ?? malhaTotalTilesInfo.minZoom ?? 0,
        keepBuffer: options.keepBuffer ?? 3,
        subdomains: malhaTotalTilesInfo.subdomains || malhaTotalTilesInfo.tilesSubdomains || [],
        getFeatureId: (properties) => properties?.segment_id || properties?.osm_id || properties?.id || null
    };

    if (options.rendererFactory) {
        layerOptions.rendererFactory = options.rendererFactory;
    }

    const vectorLayer = L.vectorGrid.protobuf(template, layerOptions);
    vectorLayer.on('loading', () => {
        atualizarCarregamento(mapId, 'Carregando tiles...', 'Malha Total (vector tiles)');
    });
    vectorLayer.on('load', () => {
        atualizarCarregamento(mapId, 'Tiles carregados', 'Malha Total pronta');
    });
    vectorLayer.on('tileerror', (err) => {
        console.warn('Erro ao carregar tile da malha total:', err);
    });

    return vectorLayer;
}

/**
 * Cria mapa temático genérico
 */
function criarMapaTematico(mapId, municipiosGeo, propriedade, label, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }
    
    console.log(`Criando mapa temático: ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);
    
    // Mesclar dados de indicadores OSM com geometria
    const municipiosComDadosOSM = anexarIndicadoresAoGeoJSON(municipiosGeo);
    
    // Mesclar dados de indicadores TOTAL com geometria
    const municipiosComDadosTotal = anexarIndicadoresTotalAoGeoJSON(municipiosGeo);
    
    // Determinar propriedade para malha total (mapeamento)
    const propriedadeTotal = propriedade === 'extensao_km' ? 'extensao_total_km' :
                             propriedade === 'densidade_area_10k' ? 'densidade_total_area_10k' :
                             propriedade === 'densidade_pop_10k' ? 'densidade_total_pop_10k' :
                             propriedade; // fallback
    
    // Calcular valores para escala de cores (OSM)
    const valoresOSM = municipiosComDadosOSM
        .map(f => f?.properties?.[propriedade])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    
    if (valoresOSM.length === 0) {
        console.warn(`Nenhum valor válido para ${propriedade}`);
        return;
    }
    
    const minValOSM = Math.min(...valoresOSM);
    const maxValOSM = Math.max(...valoresOSM);
    
    // Quebras por QUANTIS (5 classes) para melhor contraste - distribui municípios igualmente entre classes
    const breaksOSM = calcularQuantis(valoresOSM, 5);
    const colors = ['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494'];

    const getColorOSM = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        if (valor <= breaksOSM[1]) return colors[0];
        if (valor <= breaksOSM[2]) return colors[1];
        if (valor <= breaksOSM[3]) return colors[2];
        if (valor <= breaksOSM[4]) return colors[3];
        return colors[4];
    };
    
    // Criar layer OSM
    const layerOSM = L.geoJSON({type: 'FeatureCollection', features: municipiosComDadosOSM}, {
        style: (feature) => ({
            fillColor: getColorOSM(feature.properties[propriedade]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature.properties;
            const valor = props[propriedade];
            layer.bindPopup(`
                <b>${props.Municipio || props.NM_MUN}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : 'N/A'}
            `);
        }
    });
    
    // Calcular valores para escala de cores (Total)
    const valoresTotal = municipiosComDadosTotal
        .map(f => f?.properties?.[propriedadeTotal])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    
    const minValTotal = Math.min(...valoresTotal);
    const maxValTotal = Math.max(...valoresTotal);
    
    // Quebras por QUANTIS (5 classes) para melhor contraste
    const breaksTotal = calcularQuantis(valoresTotal, 5);

    const getColorTotal = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        if (valor <= breaksTotal[1]) return colors[0];
        if (valor <= breaksTotal[2]) return colors[1];
        if (valor <= breaksTotal[3]) return colors[2];
        if (valor <= breaksTotal[4]) return colors[3];
        return colors[4];
    };
    
    // Criar layer Total
    const layerTotal = L.geoJSON({type: 'FeatureCollection', features: municipiosComDadosTotal}, {
        style: (feature) => ({
            fillColor: getColorTotal(feature.properties[propriedadeTotal]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature.properties;
            const valor = props[propriedadeTotal];
            layer.bindPopup(`
                <b>${props.Municipio || props.NM_MUN}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : 'N/A'}
            `);
        }
    });
    
    // Adicionar layer OSM por padrão
    layerOSM.addTo(map);
    
    // Criar controle de camadas com duas opções
    const overlays = {
        'Malha Vicinal OSM': layerOSM,
        'Malha Total (OSM + DER)': layerTotal
    };
    
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    // Enquadrar SP completo e travar por default
    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    // Legenda externa (classes) - usando OSM por padrão
    const fmt = (v) => v.toLocaleString('pt-BR', { maximumFractionDigits: 2 });
    const legendItems = [
        { tipo: 'fill', color: colors[0], label: `${fmt(breaksOSM[0])} – ${fmt(breaksOSM[1])}` },
        { tipo: 'fill', color: colors[1], label: `${fmt(breaksOSM[1])} – ${fmt(breaksOSM[2])}` },
        { tipo: 'fill', color: colors[2], label: `${fmt(breaksOSM[2])} – ${fmt(breaksOSM[3])}` },
        { tipo: 'fill', color: colors[3], label: `${fmt(breaksOSM[3])} – ${fmt(breaksOSM[4])}` },
        { tipo: 'fill', color: colors[4], label: `${fmt(breaksOSM[4])} – ${fmt(breaksOSM[5])}` }
    ];
    renderLegendaExterna(mapId, label + ' (Malha Vicinal OSM)', legendItems);
    
    // Atualizar legenda ao trocar de camada
    map.on('overlayadd', function(e) {
        if (e.name === 'Malha Total (OSM + DER)') {
            const legendItemsTotal = [
                { tipo: 'fill', color: colors[0], label: `${fmt(breaksTotal[0])} – ${fmt(breaksTotal[1])}` },
                { tipo: 'fill', color: colors[1], label: `${fmt(breaksTotal[1])} – ${fmt(breaksTotal[2])}` },
                { tipo: 'fill', color: colors[2], label: `${fmt(breaksTotal[2])} – ${fmt(breaksTotal[3])}` },
                { tipo: 'fill', color: colors[3], label: `${fmt(breaksTotal[3])} – ${fmt(breaksTotal[4])}` },
                { tipo: 'fill', color: colors[4], label: `${fmt(breaksTotal[4])} – ${fmt(breaksTotal[5])}` }
            ];
            renderLegendaExterna(mapId, label + ' (Malha Total)', legendItemsTotal);
        }
    });
    
    map.on('overlayremove', function(e) {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaExterna(mapId, label + ' (Malha Vicinal OSM)', legendItems);
        }
    });
    
    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Cria mapa com gradiente contínuo para qualquer métrica
 * @param {string} mapId - ID do elemento do mapa
 * @param {Object} municipiosGeo - GeoJSON dos municípios
 * @param {string} propriedadeOSM - Nome da propriedade OSM (ex: 'extensao_km')
 * @param {string} propriedadeTotal - Nome da propriedade Total (ex: 'extensao_km_total')
 * @param {string} label - Rótulo para legenda (ex: 'Extensão (km)')
 * @param {Object} boundsSP - Limites geográficos de SP
 */
function criarMapaRanking(mapId, municipiosGeo, propriedadeOSM, propriedadeTotal, label, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }

    console.log(`Criando mapa ranking (gradiente contínuo): ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);

    const municipiosComDadosOSM = anexarIndicadoresAoGeoJSON(municipiosGeo);
    const municipiosComDadosTotal = anexarIndicadoresTotalAoGeoJSON(municipiosGeo);
    
    const valoresOSM = municipiosComDadosOSM
        .map(f => f?.properties?.[propriedadeOSM])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    
    const valoresTotal = municipiosComDadosTotal
        .map(f => f?.properties?.[propriedadeTotal])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);

    if (!valoresOSM.length && !valoresTotal.length) {
        console.warn(`Nenhum valor válido para ${propriedadeOSM}/${propriedadeTotal}`);
        return;
    }

    const minValOSM = Math.min(...valoresOSM);
    const maxValOSM = Math.max(...valoresOSM);
    
    const minValTotal = Math.min(...valoresTotal);
    const maxValTotal = Math.max(...valoresTotal);

    // Gradiente verde-amarelo-vermelho para extensão
    const fromColor = '#00ff00';  // Verde
    const toColor = '#ff0000';    // Vermelho
    
    // Usar mapeador percentil para melhor contraste
    const mapeadorOSM = criarMapeadorPercentil(valoresOSM);
    const mapeadorTotal = criarMapeadorPercentil(valoresTotal);
    
    const getColorOSM = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorOSM(valor);
        return interpolarHex(fromColor, toColor, t);
    };
    
    const getColorTotal = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorTotal(valor);
        return interpolarHex(fromColor, toColor, t);
    };

    const layerOSM = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosOSM }, {
        style: (feature) => ({
            fillColor: getColorOSM(feature?.properties?.[propriedadeOSM]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valor = props?.[propriedadeOSM];
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A'}
            `);
        }
    });
    
    const layerTotal = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosTotal }, {
        style: (feature) => ({
            fillColor: getColorTotal(feature?.properties?.[propriedadeTotal]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valorTotal = props?.[propriedadeTotal];
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valorTotal === 'number' ? valorTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A'}
            `);
        }
    });

    // Adicionar layer OSM por padrão
    layerOSM.addTo(map);
    
    // Criar controle de camadas com duas opções
    const overlays = {
        'Malha Vicinal OSM': layerOSM,
        'Malha Total (OSM + DER)': layerTotal
    };
    
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    // Enquadrar SP completo e travar por default
    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    // Legenda externa (gradiente vertical) - usando OSM por padrão
    renderLegendaGradienteExterna(mapId, label + ' (Malha Vicinal OSM)', minValOSM, maxValOSM, {
        fromColor: fromColor,
        toColor: toColor,
        unidade: '',
        orientation: 'vertical'
    });
    
    // Atualizar legenda ao trocar de camada
    map.on('overlayadd', function(e) {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label + ' (Malha Total)', minValTotal, maxValTotal, {
                fromColor: fromColor,
                toColor: toColor,
                unidade: '',
                orientation: 'vertical'
            });
        }
    });
    
    map.on('overlayremove', function(e) {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label + ' (Malha Vicinal OSM)', minValOSM, maxValOSM, {
                fromColor: fromColor,
                toColor: toColor,
                unidade: '',
                orientation: 'vertical'
            });
        }
    });
    
    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} (gradiente contínuo) criado!`);
}

/**
 * Cria mapa contínuo (gradiente verde-amarelo-vermelho) para extensão municipal
 */
function criarMapaRankingExtensao(mapId, municipiosGeo, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }

    console.log(`Criando mapa ranking (gradiente contínuo): ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);

    const propriedadeOSM = 'extensao_km';
    const propriedadeTotal = 'extensao_total_km';
    const label = 'km';

    const municipiosComDadosOSM = anexarIndicadoresAoGeoJSON(municipiosGeo);
    const municipiosComDadosTotal = anexarIndicadoresTotalAoGeoJSON(municipiosGeo);
    
    const valoresOSM = municipiosComDadosOSM
        .map(f => f?.properties?.extensao_km)
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    
    const valoresTotal = municipiosComDadosTotal
        .map(f => f?.properties?.extensao_total_km)
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);

    if (!valoresOSM.length && !valoresTotal.length) {
        console.warn(`Nenhum valor válido para extensão`);
        return;
    }

    const minValOSM = Math.min(...valoresOSM);
    const maxValOSM = Math.max(...valoresOSM);
    
    const minValTotal = Math.min(...valoresTotal);
    const maxValTotal = Math.max(...valoresTotal);

    // Gradiente verde-amarelo-vermelho para extensão
    const fromColor = '#00ff00';  // Verde
    const toColor = '#ff0000';    // Vermelho
    
    // Usar mapeador percentil para melhor contraste
    const mapeadorOSM = criarMapeadorPercentil(valoresOSM);
    const mapeadorTotal = criarMapeadorPercentil(valoresTotal);
    
    const getColorOSM = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorOSM(valor);
        return interpolarHex(fromColor, toColor, t);
    };
    
    const getColorTotal = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorTotal(valor);
        return interpolarHex(fromColor, toColor, t);
    };

    const layerOSM = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosOSM }, {
        style: (feature) => ({
            fillColor: getColorOSM(feature?.properties?.extensao_km),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.82
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valor = props?.extensao_km;
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' km' : 'N/A'}
            `);
        }
    });
    
    const layerTotal = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosTotal }, {
        style: (feature) => ({
            fillColor: getColorTotal(feature?.properties?.extensao_total_km),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.82
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valorTotal = props?.extensao_total_km;
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label} Total: ${typeof valorTotal === 'number' ? valorTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' km' : 'N/A'}
            `);
        }
    });

    layerOSM.addTo(map);

    const overlays = {
        'Malha Vicinal OSM': layerOSM,
        'Malha Total (OSM + DER)': layerTotal
    };
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    renderLegendaGradienteExterna(mapId, label, minValOSM, maxValOSM, { fromColor, toColor, unidade: 'km', orientation: 'vertical' });
    
    map.on('overlayadd', (e) => {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label + ' Total', minValTotal, maxValTotal, { fromColor, toColor, unidade: 'km', orientation: 'vertical' });
        }
    });
    
    map.on('overlayremove', (e) => {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label, minValOSM, maxValOSM, { fromColor, toColor, unidade: 'km', orientation: 'vertical' });
        }
    });
    
    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Cria mapa contínuo (gradiente azul-roxo-rosa) para densidade por área
 */
function criarMapaDensidadeArea(mapId, municipiosGeo, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }

    console.log(`Criando mapa densidade por área (gradiente contínuo): ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);

    const propriedadeOSM = 'densidade_area_10k';
    const propriedadeTotal = 'densidade_total_area_10k';
    const label = 'km/10.000 km²';

    const municipiosComDadosOSM = anexarIndicadoresAoGeoJSON(municipiosGeo);
    const municipiosComDadosTotal = anexarIndicadoresTotalAoGeoJSON(municipiosGeo);
    
    const valoresOSM = municipiosComDadosOSM
        .map(f => f?.properties?.[propriedadeOSM])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    
    const valoresTotal = municipiosComDadosTotal
        .map(f => f?.properties?.[propriedadeTotal])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);

    if (!valoresOSM.length && !valoresTotal.length) {
        console.warn(`Nenhum valor válido para densidade por área`);
        return;
    }

    const minValOSM = Math.min(...valoresOSM);
    const maxValOSM = Math.max(...valoresOSM);
    
    const minValTotal = Math.min(...valoresTotal);
    const maxValTotal = Math.max(...valoresTotal);

    // Gradiente azul-roxo-rosa para densidade por área
    const fromColor = '#0000ff';  // Azul
    const toColor = '#ff1493';    // Rosa escuro
    
    // Usar mapeador percentil para melhor contraste
    const mapeadorOSM = criarMapeadorPercentil(valoresOSM);
    const mapeadorTotal = criarMapeadorPercentil(valoresTotal);
    
    const getColorOSM = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorOSM(valor);
        return interpolarHex(fromColor, toColor, t);
    };
    
    const getColorTotal = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorTotal(valor);
        return interpolarHex(fromColor, toColor, t);
    };

    const layerOSM = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosOSM }, {
        style: (feature) => ({
            fillColor: getColorOSM(feature?.properties?.[propriedadeOSM]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valor = props?.[propriedadeOSM];
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A'}
            `);
        }
    });
    
    const layerTotal = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosTotal }, {
        style: (feature) => ({
            fillColor: getColorTotal(feature?.properties?.[propriedadeTotal]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valorTotal = props?.[propriedadeTotal];
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valorTotal === 'number' ? valorTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A'}
            `);
        }
    });

    layerOSM.addTo(map);
    
    const overlays = {
        'Malha Vicinal OSM': layerOSM,
        'Malha Total (OSM + DER)': layerTotal
    };
    
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    renderLegendaGradienteExterna(mapId, label, minValOSM, maxValOSM, { fromColor, toColor, unidade: '', orientation: 'vertical' });
    
    map.on('overlayadd', (e) => {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label + ' Total', minValTotal, maxValTotal, { fromColor, toColor, unidade: '', orientation: 'vertical' });
        }
    });
    
    map.on('overlayremove', (e) => {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label, minValOSM, maxValOSM, { fromColor, toColor, unidade: '', orientation: 'vertical' });
        }
    });
    
    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Cria mapa contínuo (gradiente laranja-vermelho-marrom) para densidade por população
 */
function criarMapaDensidadePop(mapId, municipiosGeo, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }

    console.log(`Criando mapa densidade por população (gradiente contínuo): ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);

    const propriedadeOSM = 'densidade_pop_10k';
    const propriedadeTotal = 'densidade_total_pop_10k';
    const label = 'km/10.000 hab';

    const municipiosComDadosOSM = anexarIndicadoresAoGeoJSON(municipiosGeo);
    const municipiosComDadosTotal = anexarIndicadoresTotalAoGeoJSON(municipiosGeo);
    
    const valoresOSM = municipiosComDadosOSM
        .map(f => f?.properties?.[propriedadeOSM])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    
    const valoresTotal = municipiosComDadosTotal
        .map(f => f?.properties?.[propriedadeTotal])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);

    if (!valoresOSM.length && !valoresTotal.length) {
        console.warn(`Nenhum valor válido para densidade por população`);
        return;
    }

    const minValOSM = Math.min(...valoresOSM);
    const maxValOSM = Math.max(...valoresOSM);
    
    const minValTotal = Math.min(...valoresTotal);
    const maxValTotal = Math.max(...valoresTotal);

    // Gradiente laranja-vermelho-marrom para densidade por população
    const fromColor = '#ffa500';  // Laranja
    const toColor = '#8b4513';    // Marrom
    
    // Usar mapeador percentil para melhor contraste
    const mapeadorOSM = criarMapeadorPercentil(valoresOSM);
    const mapeadorTotal = criarMapeadorPercentil(valoresTotal);
    
    const getColorOSM = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorOSM(valor);
        return interpolarHex(fromColor, toColor, t);
    };
    
    const getColorTotal = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = mapeadorTotal(valor);
        return interpolarHex(fromColor, toColor, t);
    };

    const layerOSM = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosOSM }, {
        style: (feature) => ({
            fillColor: getColorOSM(feature?.properties?.[propriedadeOSM]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valor = props?.[propriedadeOSM];
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A'}
            `);
        }
    });
    
    const layerTotal = L.geoJSON({ type: 'FeatureCollection', features: municipiosComDadosTotal }, {
        style: (feature) => ({
            fillColor: getColorTotal(feature?.properties?.[propriedadeTotal]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 1.0
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valorTotal = props?.[propriedadeTotal];
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valorTotal === 'number' ? valorTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A'}
            `);
        }
    });

    layerOSM.addTo(map);
    
    const overlays = {
        'Malha Vicinal OSM': layerOSM,
        'Malha Total (OSM + DER)': layerTotal
    };
    
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    renderLegendaGradienteExterna(mapId, label, minValOSM, maxValOSM, { fromColor, toColor, unidade: '', orientation: 'vertical' });
    
    map.on('overlayadd', (e) => {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label + ' Total', minValTotal, maxValTotal, { fromColor, toColor, unidade: '', orientation: 'vertical' });
        }
    });
    
    map.on('overlayremove', (e) => {
        if (e.name === 'Malha Total (OSM + DER)') {
            renderLegendaGradienteExterna(mapId, label, minValOSM, maxValOSM, { fromColor, toColor, unidade: '', orientation: 'vertical' });
        }
    });
    
    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Cria mapa Top 10
 */
function criarMapaTop10(mapId, municipiosGeo, isMaior, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }
    
    console.log(`Criando mapa Top 10 ${isMaior ? 'Maior' : 'Menor'}: ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    // Remover controles existentes
    map.eachLayer(() => {});
    defaultLayer.addTo(map);
    L.control.layers(baseLayers, null, { collapsed: true, position: 'topright' }).addTo(map);
    
    // Selecionar top 10 (apenas municípios com extensão > 0)
    const municipiosComRodovias = dadosMunicipios.filter(m => m.extensao_km > 0);
    const sorted = [...municipiosComRodovias].sort((a, b) => 
        isMaior ? b.extensao_km - a.extensao_km : a.extensao_km - b.extensao_km
    );
    const top10Codes = sorted.slice(0, 10).map(m => normalizarCodigoIbge(m.Cod_ibge)).filter(Boolean);
    
    L.geoJSON(municipiosGeo, {
        style: (feature) => {
            const cod = obterCodigoIbgeFeature(feature);
            const isTop10 = cod ? top10Codes.includes(cod) : false;
            return {
                fillColor: isTop10 ? '#e74c3c' : '#ecf0f1',
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity: isTop10 ? 0.8 : 0.2
            };
        },
        onEachFeature: (feature, layer) => {
            const cod = obterCodigoIbgeFeature(feature);
            const dadosMun = cod ? obterMapaMunicipiosPorCodigoIbge().get(cod) : null;
            if (dadosMun && cod && top10Codes.includes(cod)) {
                const ranking = top10Codes.indexOf(cod) + 1;
                layer.bindPopup(`
                    <b>#${ranking} - ${dadosMun.Municipio}</b><br>
                    Extensão: ${dadosMun.extensao_km.toLocaleString('pt-BR', {minimumFractionDigits: 2})} km
                `);
            }
        }
    }).addTo(map);

    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    renderLegendaExterna(mapId, 'Destaque', [
        { tipo: 'fill', color: '#e74c3c', label: 'Top 10' },
        { tipo: 'fill', color: '#ecf0f1', label: 'Demais municípios' }
    ]);
    
    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Cria mapa de disparidades
 */
function criarMapaDisparidades(mapId, municipiosGeo, propriedadeClasse, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }
    
    console.log(`Criando mapa de disparidades: ${mapId}...`);

    // Usar mapa do cache ou criar novo
    let map = mapasLeaflet[mapId];
    if (!map) {
        if (element._leaflet_id) {
            element._leaflet_id = null;
            element.innerHTML = '';
        }
        map = L.map(mapId, { zoomControl: false });
        mapasLeaflet[mapId] = map;
    }
    
    const { baseLayers, defaultLayer } = criarBasemaps();
    map.eachLayer(layer => {
        if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });
    defaultLayer.addTo(map);
    
    const coresClasse = {
        'Muito Abaixo': '#d73027',
        'Abaixo': '#fc8d59',
        'Média': '#fee08b',
        'Acima': '#91cf60',
        'Muito Acima': '#1a9850'
    };
    
    const municipiosComDadosOSM = anexarIndicadoresAoGeoJSON(municipiosGeo);
    const municipiosComDadosTotal = anexarIndicadoresTotalAoGeoJSON(municipiosGeo);
    
    const propriedadeTotal = propriedadeClasse.replace('classe_disp_', 'classe_total_disp_');
    
    const layerOSM = L.geoJSON({type: 'FeatureCollection', features: municipiosComDadosOSM}, {
        style: (feature) => {
            const classe = feature.properties[propriedadeClasse];
            return {
                fillColor: coresClasse[classe] || '#cccccc',
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity: 1.0
            };
        },
        onEachFeature: (feature, layer) => {
            const props = feature.properties;
            layer.bindPopup(`
                <b>${props.Municipio || props.NM_MUN}</b><br>
                Classe: ${props[propriedadeClasse] || 'N/A'}<br>
                Extensão: ${(props.extensao_km || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})} km
            `);
        }
    });
    
    const layerTotal = L.geoJSON({type: 'FeatureCollection', features: municipiosComDadosTotal}, {
        style: (feature) => {
            const classe = feature.properties[propriedadeTotal];
            return {
                fillColor: coresClasse[classe] || '#cccccc',
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity: 1.0
            };
        },
        onEachFeature: (feature, layer) => {
            const props = feature.properties;
            layer.bindPopup(`
                <b>${props.Municipio || props.NM_MUN}</b><br>
                Classe: ${props[propriedadeTotal] || 'N/A'}<br>
                Extensão Total: ${(props.extensao_total_km || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})} km
            `);
        }
    });
    
    layerOSM.addTo(map);

    const overlays = {
        'Malha Vicinal OSM': layerOSM,
        'Malha Total (OSM + DER)': layerTotal
    };
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    renderLegendaExterna(mapId, 'Classes', [
        { tipo: 'fill', color: coresClasse['Muito Acima'], label: 'Muito Acima' },
        { tipo: 'fill', color: coresClasse['Acima'], label: 'Acima' },
        { tipo: 'fill', color: coresClasse['Média'], label: 'Média' },
        { tipo: 'fill', color: coresClasse['Abaixo'], label: 'Abaixo' },
        { tipo: 'fill', color: coresClasse['Muito Abaixo'], label: 'Muito Abaixo' }
    ]);
    
    removerCarregamento(mapId);
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Inicialização principal
 */
document.addEventListener('DOMContentLoaded', async function() {
    if (document.body.dataset.page !== 'resultados') {
        console.log('🛈 Página diferente de resultados detectada; inicialização principal ignorada.');
        return;
    }
    console.log('🚀 INICIANDO PÁGINA DE RESULTADOS MUNICIPAIS...');
    
    // INICIALIZAR MAPAS IMEDIATAMENTE (mostrar basemap enquanto dados carregam)
    console.log('🗺️ Inicializando mapas instantaneamente...');
    inicializarMapasInstantaneo();
    console.log('✅ Mapas inicializados com basemap!');
    
    // Carregar dados (em paralelo com mapas já visíveis)
    const sucesso = await carregarDados();
    if (!sucesso) {
        console.error('❌ Falha ao carregar dados');
        return;
    }
    
    console.log('✅ Dados carregados, preenchendo cards...');
    
    // Preencher cards
    preencherCardsGerais();
    preencherCardsMalhaTotal();
    preencherCardsSegmentos();
    preencherCardsSegmentosTotal();
    preencherCardsMunicipais();
    preencherCardsMunicipaisTotal();
    preencherCardsDensidadeArea();
    preencherCardsDensidadeAreaTotal();
    preencherCardsDensidadePop();
    preencherCardsDensidadePopTotal();
    
    console.log('✅ Cards preenchidos, criando gráficos...');
    
    // Criar gráficos
    criarGraficoComprimentoSegmentos();
    criarGraficoTipoPavimento();
    criarGraficoFaixasExtensao();
    criarGraficosRanking();
    criarGraficoDensidadeArea();
    criarGraficoDensidadePop();
    criarGraficosDisparidades();
    
    console.log('✅ Gráficos criados!');
    console.log('📊 Status dos gráficos:', {
        segmentos: !!chartComprimentoSegmentos,
        pavimento: !!chartTipoPavimento,
        faixas: !!chartFaixasExtensao,
        ranking: !!(chartTop10Maior && chartTop10Menor),
        densidade: !!(chartDensidadeArea && chartDensidadePop),
        disparidades: !!(chartDisparidadeArea && chartDisparidadePop)
    });
    
    // CRIAR MAPAS - FORÇADO
    console.log('🗺️  INICIANDO CRIAÇÃO DE MAPAS AGORA...');
    try {
        await criarMapasBasicos();
        console.log('✅✅✅ MAPAS CRIADOS COM SUCESSO! ✅✅✅');
    } catch (err) {
        console.error('❌❌❌ ERRO CRÍTICO AO CRIAR MAPAS:', err);
        console.error('Stack trace:', err.stack);
    }
    
    // Event listeners para o toggle de disparidades
    const radioOSM = document.getElementById('disparidadeOSM');
    const radioTotal = document.getElementById('disparidadeTotal');
    
    if (radioOSM && radioTotal) {
        radioOSM.addEventListener('change', function() {
            if (this.checked) {
                console.log('Alternando para visualização: Malha Vicinal (OSM)');
                visualizacaoAtual = 'osm';
                criarGraficosDisparidades();
            }
        });
        
        radioTotal.addEventListener('change', function() {
            if (this.checked) {
                console.log('Alternando para visualização: Malha Total (OSM+DER)');
                visualizacaoAtual = 'total';
                criarGraficosDisparidades();
            }
        });
        
        console.log('✅ Event listeners do toggle de disparidades configurados');
    } else {
        console.warn('⚠️ Elementos do toggle não encontrados no DOM');
    }
    
    console.log('✅ PÁGINA CARREGADA COM SUCESSO!');
});
