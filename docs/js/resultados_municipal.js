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

// Cache para acelerar joins por código IBGE
let _dadosMunicipiosPorCodigoIbge = null;

// Flag para evitar inicialização múltipla
let paginaInicializada = false;

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
    return document.getElementById(`legenda-${mapId}`);
}

function renderLegendaExterna(mapId, titulo, items) {
    const el = getLegendaContainer(mapId);
    if (!el) {
        console.warn(`Container de legenda não encontrado para ${mapId}`);
        return;
    }

    const safeItems = Array.isArray(items) ? items.filter(Boolean) : [];
    const cols = Math.max(1, Math.min(8, safeItems.length || 1));
    el.style.setProperty('--legend-cols', String(cols));

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

    el.innerHTML = `${tituloHtml}<div class="legenda-grid">${gridItemsHtml}</div>`;
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

    const fmt = (v) => {
        if (typeof v !== 'number' || !Number.isFinite(v)) return 'N/A';
        return v.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    };

    const tituloHtml = titulo ? `<div class="legenda-titulo">${titulo}</div>` : '';
    const gradHtml = `
        <div class="legenda-gradiente">
            <div class="legenda-gradiente-bar" style="background: linear-gradient(90deg, ${fromColor}, ${toColor});"></div>
            <div class="legenda-gradiente-labels">
                <span>${fmt(minVal)}${unidade ? ` ${unidade}` : ''}</span>
                <span>${fmt(maxVal)}${unidade ? ` ${unidade}` : ''}</span>
            </div>
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

function anexarIndicadoresAoGeoJSON(municipiosGeo) {
    const mapa = obterMapaMunicipiosPorCodigoIbge();
    const features = Array.isArray(municipiosGeo?.features) ? municipiosGeo.features : [];
    return features.map(feature => {
        const codIbge = obterCodigoIbgeFeature(feature);
        const dadosMun = codIbge ? mapa.get(codIbge) : null;
        return {
            ...feature,
            properties: { ...feature.properties, ...(dadosMun || {}) }
        };
    });
}

/**
 * Carrega todos os dados necessários
 */
async function carregarDados() {
    try {
        // Carregar municípios com indicadores
        const respMun = await fetch('../data/municipios_indicadores.json');
        dadosMunicipios = await respMun.json();
        _dadosMunicipiosPorCodigoIbge = null;
        
        // Carregar regiões
        const respReg = await fetch('../data/regioes_indicadores.json');
        dadosRegioes = await respReg.json();
        
        // Carregar estatísticas completas
        const respStats = await fetch('../data/estatisticas_completas.json');
        dadosEstatisticas = await respStats.json();
        
        // Carregar estatísticas de segmentos
        const respSeg = await fetch('../data/segmentos_estatisticas.json');
        dadosSegmentos = await respSeg.json();
        
        console.log('Dados carregados:', { 
            municipios: dadosMunicipios.length, 
            regioes: dadosRegioes.length 
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
 * Cria gráfico de distribuição por comprimento de segmentos (Seção 1.2)
 */
function criarGraficoComprimentoSegmentos() {
    const ctx = document.getElementById('chartComprimentoSegmentos');
    if (!ctx) return;
    
    // Destruir gráfico existente
    if (chartComprimentoSegmentos) {
        chartComprimentoSegmentos.destroy();
    }
    
    const distribuicao = dadosSegmentos.distribuicao_por_faixas;
    
    chartComprimentoSegmentos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: distribuicao.map(d => d.faixa),
            datasets: [{
                label: 'Quantidade (segmentos)',
                data: distribuicao.map(d => d.quantidade),
                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                yAxisID: 'y'
            }, {
                label: 'Extensão (km)',
                data: distribuicao.map(d => d.extensao_km),
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                yAxisID: 'y1'
            }]
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
 * Cria gráfico de tipo de pavimento (Seção 1.3)
 */
function criarGraficoTipoPavimento() {
    const ctx = document.getElementById('chartTipoPavimento');
    if (!ctx || !dadosSegmentos.distribuicao_por_tipo.length) return;
    
    // Destruir gráfico existente
    if (chartTipoPavimento) {
        chartTipoPavimento.destroy();
    }
    
    // Ordenar por tipo alfabeticamente
    const distribuicao = dadosSegmentos.distribuicao_por_tipo
        .slice()
        .sort((a, b) => {
            const tipoA = String(a?.tipo ?? '');
            const tipoB = String(b?.tipo ?? '');
            return tipoA.localeCompare(tipoB, 'pt-BR', { sensitivity: 'base' });
        });
    
    chartTipoPavimento = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: distribuicao.map(d => {
                const tipo = d?.tipo;
                const tipoStr = (tipo === null || tipo === undefined || tipo === '') ? 'N/A' : String(tipo);
                const desc = descricaoTipoPavimento(tipo);
                return `${tipoStr} (${desc})`;
            }),
            datasets: [{
                data: distribuicao.map(d => d.percentual_extensao),
                backgroundColor: distribuicao.map(d => corTipoPavimento(d?.tipo)),
                borderColor: 'rgba(255,255,255,0.85)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'right' }
            }
        }
    });
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
    
    const contagens = faixas.map(faixa => {
        return dadosMunicipios.filter(m => 
            m.extensao_km >= faixa.min && m.extensao_km < faixa.max
        ).length;
    });
    
    chartFaixasExtensao = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faixas.map(f => f.label),
            datasets: [{
                label: 'Número de Municípios',
                data: contagens,
                backgroundColor: 'rgba(52, 152, 219, 0.7)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Municípios' } }
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
        
        chartTop10Maior = new Chart(ctxMaior, {
            type: 'bar',
            data: {
                labels: top10.map(m => m.Municipio),
                datasets: [{
                    label: 'Extensão (km)',
                    data: top10.map(m => m.extensao_km),
                    backgroundColor: 'rgba(46, 204, 113, 0.7)'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
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
        
        chartTop10Menor = new Chart(ctxMenor, {
            type: 'bar',
            data: {
                labels: bottom10.map(m => m.Municipio),
                datasets: [{
                    label: 'Extensão (km)',
                    data: bottom10.map(m => m.extensao_km),
                    backgroundColor: 'rgba(231, 76, 60, 0.7)'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }
}

/**
 * Preenche cards de densidade por área (Seção 2.1)
 */
function preencherCardsDensidadeArea() {
    const stats = dadosEstatisticas.municipal.densidade_area_10k;
    
    document.getElementById('densAreaMedia').textContent = stats.media.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densAreaMediana').textContent = stats.mediana.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densAreaMin').textContent = stats.minimo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densAreaMax').textContent = stats.maximo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
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
    
    const contagens = faixas.map(faixa => {
        return dadosMunicipios.filter(m => {
            const dens = m.densidade_area_10k;
            if (faixa.min === undefined) return dens < faixa.max;
            if (faixa.max === undefined) return dens >= faixa.min;
            return dens >= faixa.min && dens < faixa.max;
        }).length;
    });
    
    chartDensidadeArea = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faixas.map(f => f.label),
            datasets: [{
                label: 'Número de Municípios',
                data: contagens,
                backgroundColor: 'rgba(52, 152, 219, 0.7)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Municípios' } }
            }
        }
    });
}

/**
 * Preenche cards de densidade populacional (Seção 2.2)
 */
function preencherCardsDensidadePop() {
    const stats = dadosEstatisticas.municipal.densidade_pop_10k;
    
    document.getElementById('densPopMedia').textContent = stats.media.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densPopMediana').textContent = stats.mediana.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densPopMin').textContent = stats.minimo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('densPopMax').textContent = stats.maximo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
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
    
    const contagens = faixas.map(faixa => {
        return dadosMunicipios.filter(m => {
            const dens = m.densidade_pop_10k;
            if (faixa.min === undefined) return dens < faixa.max;
            if (faixa.max === undefined) return dens >= faixa.min;
            return dens >= faixa.min && dens < faixa.max;
        }).length;
    });
    
    chartDensidadePop = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faixas.map(f => f.label),
            datasets: [{
                label: 'Número de Municípios',
                data: contagens,
                backgroundColor: 'rgba(155, 89, 182, 0.7)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Municípios' } }
            }
        }
    });
}

/**
 * Cria gráficos de disparidades (Seção 2.3)
 */
function criarGraficosDisparidades() {
    // Contar por classe - disparidades espaciais
    const classesArea = {};
    dadosMunicipios.forEach(m => {
        const classe = m.classe_disp_area;
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
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
    
    // Contar por classe - disparidades populacionais
    const classesPop = {};
    dadosMunicipios.forEach(m => {
        const classe = m.classe_disp_pop;
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
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}

/**
 * Cria mapas Leaflet com dados reais
 */
async function criarMapasBasicos() {
    console.log('🗺️  Iniciando criação de mapas...');
    
    try {
        // Carregar GeoJSON dos municípios
        console.log('Carregando municipios_sp.geojson...');
        const respMunGeo = await fetch('../data/municipios_sp.geojson');
        if (!respMunGeo.ok) {
            throw new Error(`Erro ao carregar GeoJSON: ${respMunGeo.status}`);
        }
        const municipiosGeo = await respMunGeo.json();
        console.log(`✅ GeoJSON carregado: ${municipiosGeo.features.length} municípios`);

        // Bounds do estado (usado por todos os mapas para enquadrar SP completo)
        let boundsSP = null;
        try {
            boundsSP = L.geoJSON(municipiosGeo).getBounds();
        } catch (e) {
            console.warn('⚠️ Não foi possível calcular bounds do estado:', e);
        }

        // Carregar malha vicinal estimada (camada principal do estudo)
        let malhaVicinaisGeo = null;
        try {
            console.log('Carregando malha_vicinais.geojson (malha estimada)...');
            const respVicinais = await fetch('../data/malha_vicinais.geojson');
            if (respVicinais.ok) {
                malhaVicinaisGeo = await respVicinais.json();
                const nFeatures = Array.isArray(malhaVicinaisGeo?.features) ? malhaVicinaisGeo.features.length : 0;
                console.log(`✅ Malha vicinal carregada: ${nFeatures} features`);
            } else {
                console.warn(`⚠️ Não foi possível carregar malha_vicinais.geojson: HTTP ${respVicinais.status}`);
            }
        } catch (err) {
            console.warn('⚠️ Erro ao carregar malha_vicinais.geojson:', err);
        }
        
        // 1. Mapa Malha Completa
        criarMapaMalhaCompleta(municipiosGeo, malhaVicinaisGeo, boundsSP);
        
        // 2. Mapa Pavimento: malha vicinal estimada classificada por tipo
        criarMapaVicinaisPorTipo('mapaPavimento', municipiosGeo, malhaVicinaisGeo, boundsSP);
        
        // 3. Mapa Faixas de Extensão
        criarMapaTematico('mapaFaixasExtensao', municipiosGeo, 'extensao_km', 'Extensão (km)', boundsSP);
        
        // 4. Mapa ranking contínuo (gradiente)
        criarMapaRankingExtensao('mapaRankingExtensao', municipiosGeo, boundsSP);
        
        // 6. Mapa Densidade Área
        criarMapaTematico('mapaDensidadeArea', municipiosGeo, 'densidade_area_10k', 'Densidade (km/10.000km²)', boundsSP);
        
        // 7. Mapa Densidade População
        criarMapaTematico('mapaDensidadePop', municipiosGeo, 'densidade_pop_10k', 'Densidade (km/10.000 hab)', boundsSP);
        
        // 8 e 9. Mapas de Disparidades
        criarMapaDisparidades('mapaDisparidadesArea', municipiosGeo, 'classe_disp_area', boundsSP);
        criarMapaDisparidades('mapaDisparidadesPop', municipiosGeo, 'classe_disp_pop', boundsSP);
        
        console.log('✅ Todos os mapas foram criados com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao criar mapas:', error);
    }
}

function criarMapaVicinaisPorTipo(mapId, municipiosGeo, malhaVicinaisGeo, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }

    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = '';
    }

    console.log(`Criando mapa vicinais por tipo: ${mapId}...`);

    const map = L.map(mapId, { preferCanvas: true, zoomControl: false });
    const { baseLayers, defaultLayer } = criarBasemaps();
    defaultLayer.addTo(map);

    map.createPane('paneMunicipios');
    map.getPane('paneMunicipios').style.zIndex = 350;
    map.createPane('paneVicinais');
    map.getPane('paneVicinais').style.zIndex = 450;

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

    // Legenda (somente tipos presentes nos dados agregados)
    const tiposPresentes = Array.isArray(dadosSegmentos?.distribuicao_por_tipo)
        ? dadosSegmentos.distribuicao_por_tipo.map(d => String(d?.tipo ?? '')).filter(t => t !== '')
        : [];
    const uniqueTipos = Array.from(new Set(tiposPresentes));
    uniqueTipos.sort((a, b) => a.localeCompare(b, 'pt-BR', { numeric: true }));

    // Controle de camadas (basemap + overlays)
    const overlays = { 'Municípios (referência)': layerMunicipios };
    if (layerVicinais) overlays['Vicinais (por tipo)'] = layerVicinais;
    L.control.layers(baseLayers, overlays, { collapsed: true, position: 'topright' }).addTo(map);

    // Enquadrar SP completo e travar por default
    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    // Legenda externa (somente tipos presentes nos dados agregados)
    const legendItems = uniqueTipos.map(t => ({
        tipo: 'line',
        color: corTipoPavimento(t),
        label: `${t} (${descricaoTipoPavimento(t)})`
    }));
    renderLegendaExterna(mapId, 'Tipo (descrição)', legendItems);

    console.log(`✅ Mapa ${mapId} (vicinais por tipo) criado!`);
}

/**
 * Cria mapa da malha completa
 */
function criarMapaMalhaCompleta(municipiosGeo, malhaVicinaisGeo, boundsSP) {
    const element = document.getElementById('mapaMalhaCompleta');
    if (!element) {
        console.error('Elemento mapaMalhaCompleta não encontrado!');
        return;
    }
    
    console.log('Criando mapa malha completa...');
    
    // Evitar erro de "Map container is already initialized" em caso de re-init
    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = '';
    }

    const map = L.map('mapaMalhaCompleta', { preferCanvas: true, zoomControl: false });
    const { baseLayers, defaultLayer } = criarBasemaps();
    defaultLayer.addTo(map);

    map.createPane('paneMunicipios');
    map.getPane('paneMunicipios').style.zIndex = 400;
    map.createPane('paneVicinais');
    map.getPane('paneVicinais').style.zIndex = 450;
    
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

    // Adicionar camada principal: malha vicinal estimada
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

    // Controle de camadas (basemap + overlays) (deixar a malha estimada ligada por padrão)
    const overlays = {
        'Municípios (referência)': layerMunicipios
    };
    if (layerVicinais) {
        overlays['Malha vicinal estimada (principal)'] = layerVicinais;
    }
    L.control.layers(baseLayers, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    // Enquadrar SP completo e travar por default
    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    // Legenda externa
    const legendItems = [
        { tipo: 'fill', color: '#3498db', label: 'Municípios (referência)' },
        { tipo: 'line', color: '#e67e22', label: 'Malha vicinal estimada (principal)' }
    ];
    renderLegendaExterna('mapaMalhaCompleta', 'Camadas', legendItems);
    
    console.log('✅ Mapa malha completa criado com sucesso!');
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

    // Evitar erro de "Map container is already initialized" em reinit
    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = '';
    }
    
    const map = L.map(mapId, { zoomControl: false });
    const { baseLayers, defaultLayer } = criarBasemaps();
    defaultLayer.addTo(map);
    L.control.layers(baseLayers, null, { collapsed: true, position: 'topright' }).addTo(map);
    
    // Mesclar dados de indicadores com geometria
    const municipiosComDados = anexarIndicadoresAoGeoJSON(municipiosGeo);
    
    // Calcular valores para escala de cores
    const valores = municipiosComDados
        .map(f => f?.properties?.[propriedade])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
    
    if (valores.length === 0) {
        console.warn(`Nenhum valor válido para ${propriedade}`);
        return;
    }
    
    const minVal = Math.min(...valores);
    const maxVal = Math.max(...valores);
    
    // Quebras (5 classes) e função de cor
    const range = (maxVal - minVal) || 1;
    const breaks = [
        minVal,
        minVal + range * 0.2,
        minVal + range * 0.4,
        minVal + range * 0.6,
        minVal + range * 0.8,
        maxVal
    ];
    const colors = ['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494'];

    const getColor = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        if (valor <= breaks[1]) return colors[0];
        if (valor <= breaks[2]) return colors[1];
        if (valor <= breaks[3]) return colors[2];
        if (valor <= breaks[4]) return colors[3];
        return colors[4];
    };
    
    L.geoJSON({type: 'FeatureCollection', features: municipiosComDados}, {
        style: (feature) => ({
            fillColor: getColor(feature.properties[propriedade]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.7
        }),
        onEachFeature: (feature, layer) => {
            const props = feature.properties;
            const valor = props[propriedade];
            layer.bindPopup(`
                <b>${props.Municipio || props.NM_MUN}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : 'N/A'}
            `);
        }
    }).addTo(map);

    // Enquadrar SP completo e travar por default
    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    // Legenda externa (classes)
    const fmt = (v) => v.toLocaleString('pt-BR', { maximumFractionDigits: 2 });
    const legendItems = [
        { tipo: 'fill', color: colors[0], label: `${fmt(breaks[0])} – ${fmt(breaks[1])}` },
        { tipo: 'fill', color: colors[1], label: `${fmt(breaks[1])} – ${fmt(breaks[2])}` },
        { tipo: 'fill', color: colors[2], label: `${fmt(breaks[2])} – ${fmt(breaks[3])}` },
        { tipo: 'fill', color: colors[3], label: `${fmt(breaks[3])} – ${fmt(breaks[4])}` },
        { tipo: 'fill', color: colors[4], label: `${fmt(breaks[4])} – ${fmt(breaks[5])}` }
    ];
    renderLegendaExterna(mapId, label, legendItems);
    
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Cria mapa contínuo (gradiente) para extensão municipal (Seção 1.5)
 */
function criarMapaRankingExtensao(mapId, municipiosGeo, boundsSP) {
    const element = document.getElementById(mapId);
    if (!element) {
        console.warn(`Elemento ${mapId} não encontrado!`);
        return;
    }

    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = '';
    }

    console.log(`Criando mapa ranking (gradiente contínuo): ${mapId}...`);

    const map = L.map(mapId, { zoomControl: false });
    const { baseLayers, defaultLayer } = criarBasemaps();
    defaultLayer.addTo(map);
    L.control.layers(baseLayers, null, { collapsed: true, position: 'topright' }).addTo(map);

    const propriedade = 'extensao_km';
    const label = 'Extensão (km)';

    const municipiosComDados = anexarIndicadoresAoGeoJSON(municipiosGeo);
    const valores = municipiosComDados
        .map(f => f?.properties?.[propriedade])
        .filter(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);

    if (!valores.length) {
        console.warn(`Nenhum valor válido para ${propriedade}`);
        return;
    }

    const minVal = Math.min(...valores);
    const maxVal = Math.max(...valores);
    const denom = (maxVal - minVal) || 1;

    const fromColor = '#ffffcc';
    const toColor = '#253494';
    const getColor = (valor) => {
        if (typeof valor !== 'number' || !Number.isFinite(valor)) return '#e0e0e0';
        const t = (valor - minVal) / denom;
        return interpolarHex(fromColor, toColor, t);
    };

    L.geoJSON({ type: 'FeatureCollection', features: municipiosComDados }, {
        style: (feature) => ({
            fillColor: getColor(feature?.properties?.[propriedade]),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.82
        }),
        onEachFeature: (feature, layer) => {
            const props = feature?.properties || {};
            const valor = props?.[propriedade];
            const nome = props.Municipio || props.NM_MUN || 'Município';
            layer.bindPopup(`
                <b>${nome}</b><br>
                ${label}: ${typeof valor === 'number' ? valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' km' : 'N/A'}
            `);
        }
    }).addTo(map);

    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    renderLegendaGradienteExterna(mapId, label, minVal, maxVal, { fromColor, toColor, unidade: 'km' });
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

    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = '';
    }
    
    const map = L.map(mapId, { zoomControl: false });
    const { baseLayers, defaultLayer } = criarBasemaps();
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

    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = '';
    }
    
    const map = L.map(mapId, { zoomControl: false });
    const { baseLayers, defaultLayer } = criarBasemaps();
    defaultLayer.addTo(map);
    L.control.layers(baseLayers, null, { collapsed: true, position: 'topright' }).addTo(map);
    
    const coresClasse = {
        'Muito Abaixo': '#d73027',
        'Abaixo': '#fc8d59',
        'Média': '#fee08b',
        'Acima': '#91cf60',
        'Muito Acima': '#1a9850'
    };
    
    // Mesclar dados
    const municipiosComDados = anexarIndicadoresAoGeoJSON(municipiosGeo);
    
    L.geoJSON({type: 'FeatureCollection', features: municipiosComDados}, {
        style: (feature) => {
            const classe = feature.properties[propriedadeClasse];
            return {
                fillColor: coresClasse[classe] || '#cccccc',
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity: 0.7
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
    }).addTo(map);

    aplicarEnquadramentoSP(map, boundsSP);
    const viewState = boundsSP ? { center: boundsSP.getCenter(), zoom: map.getZoom() } : { center: map.getCenter(), zoom: map.getZoom() };
    adicionarControleTravamento(map, viewState);

    renderLegendaExterna(mapId, 'Classes', [
        { tipo: 'fill', color: coresClasse['Muito Abaixo'], label: 'Muito Abaixo' },
        { tipo: 'fill', color: coresClasse['Abaixo'], label: 'Abaixo' },
        { tipo: 'fill', color: coresClasse['Média'], label: 'Média' },
        { tipo: 'fill', color: coresClasse['Acima'], label: 'Acima' },
        { tipo: 'fill', color: coresClasse['Muito Acima'], label: 'Muito Acima' }
    ]);
    
    console.log(`✅ Mapa ${mapId} criado!`);
}

/**
 * Inicialização principal
 */
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 INICIANDO PÁGINA DE RESULTADOS MUNICIPAIS...');
    
    // Carregar dados
    const sucesso = await carregarDados();
    if (!sucesso) {
        console.error('❌ Falha ao carregar dados');
        return;
    }
    
    console.log('✅ Dados carregados, preenchendo cards...');
    
    // Preencher cards
    preencherCardsGerais();
    preencherCardsSegmentos();
    preencherCardsMunicipais();
    preencherCardsDensidadeArea();
    preencherCardsDensidadePop();
    
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
});
