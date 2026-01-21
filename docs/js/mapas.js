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

const COLOR_RAMPS = {
    continuous: {
        viridis: {label: 'Viridis', colors: ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']},
        blues: {label: 'Blues', colors: ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#08306b']},
        reds: {label: 'Reds', colors: ['#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d']},
        greens: {label: 'Greens', colors: ['#f7fcf5', '#c7e9c0', '#74c476', '#238b45', '#00441b']},
        oranges: {label: 'Oranges', colors: ['#fff5eb', '#fdd0a2', '#fd8d3c', '#d94801', '#7f2704']},
        purples: {label: 'Purples', colors: ['#fcfbfd', '#dadaeb', '#9e9ac8', '#6a51a3', '#3f007d']},
        plasma: {label: 'Plasma', colors: ['#0d0887', '#7e03a8', '#cc4778', '#f89540', '#f0f921']},
        inferno: {label: 'Inferno', colors: ['#000004', '#420a68', '#932667', '#dd513a', '#fca50a']},
        magma: {label: 'Magma', colors: ['#000004', '#3b0f70', '#8c2981', '#de4968', '#febb81']},
        cividis: {label: 'Cividis', colors: ['#00224e', '#123570', '#3b496c', '#575d6d', '#707173']},
        spectral: {label: 'Spectral', colors: ['#9e0142', '#f46d43', '#fdae61', '#66c2a5', '#5e4fa2']},
        coolwarm: {label: 'Cool-Warm', colors: ['#3b4cc0', '#7092c0', '#c0c0c0', '#d68a7b', '#b40426']},
        rdylgn: {label: 'Red-Yellow-Green', colors: ['#a50026', '#f46d43', '#ffffbf', '#74add1', '#313695']},
        ylgnbu: {label: 'Yellow-Green-Blue', colors: ['#ffffd9', '#c7e9b4', '#41b6c4', '#225ea8', '#081d58']}
    },
    discrete: {
        set1: {label: 'Set1', colors: ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf']},
        set2: {label: 'Set2', colors: ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3']},
        set3: {label: 'Set3', colors: ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5']},
        tableau: {label: 'Tableau 10', colors: ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7']},
        paired: {label: 'Paired', colors: ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00']},
        dark2: {label: 'Dark2', colors: ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666']},
        accent: {label: 'Accent', colors: ['#7fc97f', '#beaed4', '#fdc086', '#ffff99', '#386cb0', '#f0027f', '#bf5b17', '#666666']},
        pastel: {label: 'Pastel', colors: ['#b3e2cd', '#fdcdac', '#cbd5e8', '#f4cae4', '#e6f5c9', '#fff2ae', '#f1e2cc', '#cccccc']},
        bold: {label: 'Bold', colors: ['#7f3c8d', '#11a579', '#3969ac', '#f2b701', '#e73f74', '#80ba5a', '#e68310', '#008695']}
    }
};

function hexToRgb(hex) {
    const h = hex.replace('#', '').trim();
    const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h;
    const n = parseInt(full, 16);
    return {r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255};
}

function rgbToHex({r, g, b}) {
    const to = (v) => v.toString(16).padStart(2, '0');
    return `#${to(r)}${to(g)}${to(b)}`;
}

function lerp(a, b, t) {
    return a + (b - a) * t;
}

function sampleRampColor(stops, t) {
    if (!Array.isArray(stops) || !stops.length) return '#999999';
    if (stops.length === 1) return stops[0];
    const clamped = Math.max(0, Math.min(1, t));
    const seg = (stops.length - 1) * clamped;
    const idx = Math.floor(seg);
    const frac = seg - idx;
    const c1 = hexToRgb(stops[idx]);
    const c2 = hexToRgb(stops[Math.min(stops.length - 1, idx + 1)]);
    const rgb = {
        r: Math.round(lerp(c1.r, c2.r, frac)),
        g: Math.round(lerp(c1.g, c2.g, frac)),
        b: Math.round(lerp(c1.b, c2.b, frac))
    };
    return rgbToHex(rgb);
}

function computeDescriptiveStats(values) {
    const nums = values
        .map(v => Number(v))
        .filter(v => !Number.isNaN(v) && Number.isFinite(v));
    const n = nums.length;
    if (!n) return null;

    let min = nums[0];
    let max = nums[0];
    // Welford
    let mean = 0;
    let m2 = 0;
    let k = 0;
    for (const x of nums) {
        k += 1;
        if (x < min) min = x;
        if (x > max) max = x;
        const delta = x - mean;
        mean += delta / k;
        const delta2 = x - mean;
        m2 += delta * delta2;
    }
    const variance = m2 / n;
    const stdDev = Math.sqrt(variance);

    const sorted = nums.slice().sort((a, b) => a - b);
    const mid = Math.floor(n / 2);
    const median = n % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;

    // Moda: se poucos únicos, calcular exato; senão, aproximar por bins
    let modeLabel = null;
    const uniqueCounts = new Map();
    for (const x of nums) {
        if (uniqueCounts.size > 60) break;
        const key = Number.isInteger(x) ? String(x) : x.toFixed(2);
        uniqueCounts.set(key, (uniqueCounts.get(key) || 0) + 1);
    }
    if (uniqueCounts.size <= 60) {
        let bestKey = null;
        let bestCount = -1;
        for (const [key, count] of uniqueCounts.entries()) {
            if (count > bestCount) {
                bestCount = count;
                bestKey = key;
            }
        }
        modeLabel = bestKey;
    } else {
        const bins = 20;
        const width = (max - min) / bins;
        const counts = Array.from({length: bins}, () => 0);
        for (const x of nums) {
            const idx = Math.max(0, Math.min(bins - 1, Math.floor((x - min) / width)));
            counts[idx] += 1;
        }
        let bestIdx = 0;
        for (let i = 1; i < bins; i += 1) {
            if (counts[i] > counts[bestIdx]) bestIdx = i;
        }
        const from = min + bestIdx * width;
        const to = min + (bestIdx + 1) * width;
        modeLabel = `${from.toLocaleString('pt-BR', {maximumFractionDigits: 2})} – ${to.toLocaleString('pt-BR', {maximumFractionDigits: 2})}`;
    }

    return {n, min, max, mean, median, mode: modeLabel, stdDev, variance, sum: nums.reduce((a, b) => a + b, 0)};
}

function createStatsPanel(mapId, overlayLayers, overlayItems, map) {
    // Buscar elementos existentes no HTML ao invés de criar novos
    const panel = document.getElementById(`${mapId}-layer-info`);
    if (!panel) return null;

    const statsBox = panel.querySelector('.stats-layers');
    if (!statsBox) return null;

    const layerSelect = document.getElementById(`${mapId}-stats-layer`);
    const attrSelect = document.getElementById(`${mapId}-stats-attr`);
    const applyBtn = document.getElementById(`${mapId}-stats-apply`);
    const output = document.getElementById(`${mapId}-stats-output`);
    if (!layerSelect || !attrSelect || !applyBtn || !output) return null;

    const layerOptions = overlayItems
        .map(item => ({key: item.key, label: item.label}))
        .filter(item => overlayLayers[item.key]);
    layerSelect.innerHTML = '';
    layerOptions.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.key;
        opt.textContent = item.label;
        layerSelect.appendChild(opt);
    });

    const refreshAttributes = () => {
        attrSelect.innerHTML = '';
        const key = layerSelect.value;
        const layer = overlayLayers[key];
        const features = getLayerFeatures(layer, 800);
        const attrs = collectAttributeKeys(features);
        attrs.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a;
            opt.textContent = a;
            attrSelect.appendChild(opt);
        });
        if (!attrs.length) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'Sem atributos';
            attrSelect.appendChild(opt);
        }
    };

    const renderStats = () => {
        output.innerHTML = '';
        const layerKey = layerSelect.value;
        const attr = attrSelect.value;
        const layer = overlayLayers[layerKey];
        if (!layer || !attr) {
            output.innerHTML = '<p>Selecione camada e atributo.</p>';
            return;
        }
        if (map && typeof map.hasLayer === 'function' && !map.hasLayer(layer)) {
            output.innerHTML = '<p>Ative a camada no mapa para calcular.</p>';
            return;
        }
        const features = getLayerFeatures(layer, 6000);
        const values = features.map(f => f?.properties?.[attr]).filter(v => v !== undefined && v !== null && v !== '');
        const stats = computeDescriptiveStats(values);
        if (!stats) {
            output.innerHTML = '<p>Sem valores numéricos suficientes.</p>';
            return;
        }
        const fmt = (v) => Number(v).toLocaleString('pt-BR', {maximumFractionDigits: 4});
        output.innerHTML = `
            <div class="stats-grid">
                <div><span class="k">contagem (n)</span><span class="v">${stats.n.toLocaleString('pt-BR')}</span></div>
                <div><span class="k">somatório</span><span class="v">${fmt(stats.sum)}</span></div>
                <div><span class="k">mínimo</span><span class="v">${fmt(stats.min)}</span></div>
                <div><span class="k">máximo</span><span class="v">${fmt(stats.max)}</span></div>
                <div><span class="k">média</span><span class="v">${fmt(stats.mean)}</span></div>
                <div><span class="k">mediana</span><span class="v">${fmt(stats.median)}</span></div>
                <div><span class="k">moda</span><span class="v">${stats.mode ?? '—'}</span></div>
                <div><span class="k">desvio padrão</span><span class="v">${fmt(stats.stdDev)}</span></div>
                <div><span class="k">variância</span><span class="v">${fmt(stats.variance)}</span></div>
            </div>
        `;
    };

    layerSelect.addEventListener('change', () => {
        refreshAttributes();
        output.innerHTML = '';
    });
    applyBtn.addEventListener('click', renderStats);

    refreshAttributes();
    return statsBox;
}

function getLayerFeatures(layer, limit = 800) {
    if (!layer) return [];

    // Preferir amostragem via eachLayer() para evitar materializar GeoJSON gigante
    if (typeof layer.eachLayer === 'function') {
        const features = [];
        layer.eachLayer(l => {
            if (features.length >= limit) return;
            const f = l?.feature;
            if (f?.properties) features.push(f);
        });
        return features;
    }

    if (typeof layer.toGeoJSON !== 'function') return [];
    const geo = layer.toGeoJSON();
    if (!Array.isArray(geo.features)) return [];
    return geo.features.slice(0, limit);
}

function collectAttributeKeys(features) {
    const keys = new Set();
    features.forEach(f => {
        if (!f || !f.properties) return;
        Object.keys(f.properties).forEach(k => keys.add(k));
    });
    return Array.from(keys).sort((a, b) => a.localeCompare(b, 'pt-BR'));
}

function inferAttributeType(features, attr) {
    let numericCount = 0;
    let textCount = 0;
    for (const f of features) {
        const val = f?.properties?.[attr];
        if (val === null || val === undefined || val === '') continue;
        const num = Number(val);
        if (!Number.isNaN(num) && Number.isFinite(num)) {
            numericCount += 1;
        } else {
            textCount += 1;
        }
        if (numericCount + textCount >= 20) break;
    }
    return numericCount >= textCount ? 'numeric' : 'text';
}

function buildLegendSpec(layer, attr, typeChoice, mode, rampKey) {
    const features = getLayerFeatures(layer, 2000);
    if (!features.length || !attr) return null;

    const geomKind = (() => {
        for (const f of features) {
            const t = f?.geometry?.type;
            if (!t) continue;
            if (t.includes('Polygon')) return 'polygon';
            if (t.includes('LineString')) return 'line';
            if (t.includes('Point')) return 'point';
        }
        return 'line';
    })();

    const makeStyle = (color, missing = false) => {
        const c = missing ? '#9e9e9e' : color;
        if (geomKind === 'polygon') {
            return {
                color: c,
                weight: 1,
                opacity: missing ? 0.25 : 0.7,
                fillColor: c,
                fillOpacity: missing ? 0.08 : 0.35
            };
        }
        // line / point: usar estilo de linha (point vira marcador padrão do GeoJSON, mas aqui é só fallback)
        return {
            color: c,
            weight: missing ? 0.8 : 2.0,
            opacity: missing ? 0.25 : 0.85
        };
    };

    const rawValues = features
        .map(f => f?.properties?.[attr])
        .filter(v => v !== undefined && v !== null && v !== '');
    if (!rawValues.length) return null;

    const inferred = inferAttributeType(features, attr);
    const resolvedType = typeChoice === 'auto' ? inferred : typeChoice;

    // Texto (categorizado)
    if (resolvedType === 'text') {
        const unique = Array.from(new Set(rawValues.map(v => String(v))));
        unique.sort((a, b) => a.localeCompare(b, 'pt-BR'));
        const maxCats = 12;
        const cats = unique.slice(0, maxCats);
        const palette = (COLOR_RAMPS.discrete[rampKey]?.colors || COLOR_RAMPS.discrete.set1.colors);
        const colors = cats.map((_, i) => palette[i % palette.length]);
        const mapping = new Map(cats.map((c, i) => [c, colors[i]]));

        const items = cats.map((c, i) => ({label: c, color: colors[i]}));
        const styleFn = (feature) => {
            const v = feature?.properties?.[attr];
            const key = v === undefined || v === null ? '' : String(v);
            const color = mapping.get(key) || '#9e9e9e';
            return makeStyle(color, !mapping.get(key));
        };
        return {type: 'text', mode: 'discrete', items, styleFn, geomKind};
    }

    // Numérico (graduado)
    const nums = rawValues.map(v => Number(v)).filter(v => !Number.isNaN(v) && Number.isFinite(v));
    if (!nums.length) return null;

    const sorted = nums.slice().sort((a, b) => a - b);
    const min = sorted[0];
    const max = sorted[sorted.length - 1];
    if (min === max) {
        const singleColor = (COLOR_RAMPS.continuous[rampKey]?.colors || COLOR_RAMPS.continuous.viridis.colors).slice(-1)[0];
        const items = [{label: `${min.toLocaleString('pt-BR')}`, color: singleColor}];
        const styleFn = () => makeStyle(singleColor, false);
        return {type: 'numeric', mode, items, styleFn, geomKind};
    }

    const steps = 5;
    if (mode === 'continuous') {
        const stops = (COLOR_RAMPS.continuous[rampKey]?.colors || COLOR_RAMPS.continuous.viridis.colors);
        const ticks = [0, 0.25, 0.5, 0.75, 1].map(t => ({
            t,
            v: min + (max - min) * t,
            color: sampleRampColor(stops, t)
        }));
        const items = ticks.map(x => ({
            label: x.v.toLocaleString('pt-BR', {maximumFractionDigits: 2}),
            color: x.color
        }));
        const styleFn = (feature) => {
            const v0 = feature?.properties?.[attr];
            const v = Number(v0);
            if (Number.isNaN(v) || !Number.isFinite(v)) return makeStyle('#9e9e9e', true);
            const t = (v - min) / (max - min);
            const color = sampleRampColor(stops, t);
            return makeStyle(color, false);
        };
        return {type: 'numeric', mode: 'continuous', items, styleFn, geomKind};
    }

    // Discreta: quantis
    const palette = (COLOR_RAMPS.discrete[rampKey]?.colors || COLOR_RAMPS.discrete.tableau.colors);
    const colors = Array.from({length: steps}, (_, i) => palette[i % palette.length]);
    const breaks = [min];
    for (let i = 1; i < steps; i += 1) {
        const idx = Math.floor((sorted.length * i) / steps);
        breaks.push(sorted[Math.min(sorted.length - 1, idx)]);
    }
    breaks.push(max);

    const items = [];
    for (let i = 0; i < steps; i += 1) {
        const from = breaks[i];
        const to = breaks[i + 1];
        items.push({
            label: `${from.toLocaleString('pt-BR', {maximumFractionDigits: 2})} – ${to.toLocaleString('pt-BR', {maximumFractionDigits: 2})}`,
            color: colors[i]
        });
    }
    const styleFn = (feature) => {
        const v0 = feature?.properties?.[attr];
        const v = Number(v0);
        if (Number.isNaN(v) || !Number.isFinite(v)) return makeStyle('#9e9e9e', true);
        for (let i = 0; i < steps; i += 1) {
            if (v <= breaks[i + 1]) {
                const color = colors[i];
                return makeStyle(color, false);
            }
        }
        const last = colors[colors.length - 1];
        return makeStyle(last, false);
    };
    return {type: 'numeric', mode: 'discrete', items, styleFn, geomKind};
}

function createLegendPanel(mapId, overlayLayers, overlayItems, map) {
    // Buscar elementos existentes no HTML ao invés de criar novos
    const panel = document.getElementById(`${mapId}-layer-info`);
    if (!panel) return null;

    const legendBox = panel.querySelector('.legend-panel');
    if (!legendBox) return null;

    const layerSelect = document.getElementById(`${mapId}-legend-layer`);
    const attrSelect = document.getElementById(`${mapId}-legend-attr`);
    const typeSelect = document.getElementById(`${mapId}-legend-type`);
    const modeSelect = document.getElementById(`${mapId}-legend-mode`);
    const rampSelect = document.getElementById(`${mapId}-legend-ramp`);
    const rampPreview = document.getElementById(`${mapId}-ramp-preview`);
    const output = document.getElementById(`${mapId}-legend-output`);
    const applyBtn = document.getElementById(`${mapId}-legend-apply`);

    if (!layerSelect || !attrSelect || !typeSelect || !modeSelect || !rampSelect || !output || !applyBtn) return null;

    const layerOptions = overlayItems
        .map(item => ({key: item.key, label: item.label}))
        .filter(item => overlayLayers[item.key]);

    layerSelect.innerHTML = '';
    layerOptions.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.key;
        opt.textContent = item.label;
        layerSelect.appendChild(opt);
    });

    const updateRampPreview = () => {
        if (!rampPreview) return;
        const mode = modeSelect.value;
        const rampKey = rampSelect.value;
        const ramps = mode === 'continuous' ? COLOR_RAMPS.continuous : COLOR_RAMPS.discrete;
        const meta = ramps[rampKey];
        if (!meta) {
            rampPreview.innerHTML = '';
            return;
        }
        const colors = meta.colors;
        if (mode === 'continuous') {
            // Gradient contínuo
            const gradient = `linear-gradient(to right, ${colors.join(', ')})`;
            rampPreview.innerHTML = `
                <div class="ramp-bar" style="background: ${gradient};"></div>
                <span class="ramp-label">${meta.label}</span>
            `;
        } else {
            // Blocos discretos
            const blockWidth = 100 / colors.length;
            const blocks = colors.map(c => 
                `<span class="ramp-block" style="background: ${c}; width: ${blockWidth}%;"></span>`
            ).join('');
            rampPreview.innerHTML = `
                <div class="ramp-bar ramp-discrete">${blocks}</div>
                <span class="ramp-label">${meta.label}</span>
            `;
        }
    };

    const populateRampOptions = () => {
        const mode = modeSelect.value;
        rampSelect.innerHTML = '';
        const ramps = mode === 'continuous' ? COLOR_RAMPS.continuous : COLOR_RAMPS.discrete;
        Object.entries(ramps).forEach(([key, meta]) => {
            const opt = document.createElement('option');
            opt.value = key;
            opt.textContent = meta.label;
            rampSelect.appendChild(opt);
        });
        updateRampPreview();
    };

    const getResolvedDataType = () => {
        const typeChoice = typeSelect.value;
        if (typeChoice !== 'auto') return typeChoice;
        const layerKey = layerSelect.value;
        const attr = attrSelect.value;
        const layer = overlayLayers[layerKey];
        if (!layer || !attr) return 'text';
        const features = getLayerFeatures(layer, 300);
        return inferAttributeType(features, attr);
    };

    const enforceLegendByDataType = () => {
        const resolved = getResolvedDataType();
        // Texto: legenda categorizada => discreta apenas
        if (resolved === 'text') {
            modeSelect.value = 'discrete';
            modeSelect.disabled = true;
        } else {
            modeSelect.disabled = false;
        }
        populateRampOptions();
    };

    const refreshAttributes = () => {
        attrSelect.innerHTML = '';
        const key = layerSelect.value;
        const features = getLayerFeatures(overlayLayers[key], 800);
        const attrs = collectAttributeKeys(features);
        attrs.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a;
            opt.textContent = a;
            attrSelect.appendChild(opt);
        });
        if (!attrs.length) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'Sem atributos';
            attrSelect.appendChild(opt);
        }
    };

    const renderLegend = () => {
        output.innerHTML = '';
        const layerKey = layerSelect.value;
        const attr = attrSelect.value;
        if (!overlayLayers[layerKey] || !attr) {
            output.innerHTML = '<p>Sem dados para gerar legenda.</p>';
            return;
        }

        const spec = buildLegendSpec(
            overlayLayers[layerKey],
            attr,
            typeSelect.value,
            modeSelect.value,
            rampSelect.value
        );
        if (!spec || !spec.items?.length) {
            output.innerHTML = '<p>Sem valores suficientes para legenda.</p>';
            return;
        }
        const list = document.createElement('ul');
        list.className = 'legend-list';
        spec.items.forEach(item => {
            const li = document.createElement('li');
            li.className = 'legend-item';
            const swatch = document.createElement('span');
            swatch.className = 'legend-swatch';
            swatch.style.backgroundColor = item.color;
            const label = document.createElement('span');
            label.textContent = item.label;
            li.appendChild(swatch);
            li.appendChild(label);
            list.appendChild(li);
        });
        output.appendChild(list);
    };

    const injectLegendIntoLayerControl = (layerKey, items) => {
        const layerCtl = panel.querySelector('.layer-control');
        const li = layerCtl?.querySelector(`.layer-item[data-key="${layerKey}"]`);
        const host = li?.querySelector('.layer-legend');
        if (!host) return;

        const symbol = overlayItems.find(o => o.key === layerKey)?.symbol || '';

        host.innerHTML = '';
        const list = document.createElement('ul');
        list.className = 'legend-list legend-list-inline';
        items.forEach(item => {
            const row = document.createElement('li');
            row.className = 'legend-item';
            const swatch = document.createElement('span');
            // Usar o MESMO tipo de símbolo da camada (linha/polígono)
            // e apenas pintar com a cor da classe gerada.
            swatch.className = `layer-symbol legend-symbol ${symbol}`;
            swatch.style.backgroundColor = item.color;
            swatch.style.borderColor = item.color;
            const label = document.createElement('span');
            label.textContent = item.label;
            row.appendChild(swatch);
            row.appendChild(label);
            list.appendChild(row);
        });
        host.appendChild(list);
    };

    const applyLegendToMap = () => {
        const layerKey = layerSelect.value;
        const attr = attrSelect.value;
        const layer = overlayLayers[layerKey];
        if (!layer || !attr) return;

        if (map && typeof map.hasLayer === 'function' && !map.hasLayer(layer)) {
            output.innerHTML = '<p>Ative a camada no mapa para aplicar a legenda.</p>';
            return;
        }

        const spec = buildLegendSpec(layer, attr, typeSelect.value, modeSelect.value, rampSelect.value);
        if (!spec || !spec.items?.length || typeof spec.styleFn !== 'function') {
            output.innerHTML = '<p>Não foi possível gerar/aplicar a legenda.</p>';
            return;
        }

        if (typeof layer.setStyle === 'function') {
            layer.setStyle(spec.styleFn);
        }

        injectLegendIntoLayerControl(layerKey, spec.items);
        renderLegend();
    };

    layerSelect.addEventListener('change', () => {
        refreshAttributes();
        enforceLegendByDataType();
        renderLegend();
    });
    attrSelect.addEventListener('change', () => {
        enforceLegendByDataType();
        renderLegend();
    });
    typeSelect.addEventListener('change', () => {
        enforceLegendByDataType();
        renderLegend();
    });
    modeSelect.addEventListener('change', () => {
        enforceLegendByDataType();
        renderLegend();
    });
    rampSelect.addEventListener('change', () => {
        updateRampPreview();
        renderLegend();
    });
    applyBtn.addEventListener('click', applyLegendToMap);

    populateRampOptions();
    refreshAttributes();
    enforceLegendByDataType();
    renderLegend();
}

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

        // Variável para rastrear basemap atual
        let currentBasemap = baseMaps['OpenStreetMap'];

        // Popular elementos HTML existentes ao invés de criar controle Leaflet
        const layerList = document.getElementById(`${mapId}-layer-list`);
        const basemapSelect = document.getElementById(`${mapId}-basemap-select`);

        if (layerList) {
            layerList.innerHTML = overlayItems.map(item => `
                <li class="layer-item" data-key="${item.key}" draggable="true">
                    <label>
                        <span class="layer-row">
                            <input type="checkbox" id="${mapId}-chk-${item.key}" checked>
                            <span class="layer-label">${item.label}</span>
                        </span>
                        <span class="layer-symbol ${item.symbol}"></span>
                        <div class="layer-legend" aria-live="polite"></div>
                    </label>
                </li>
            `).join('');
        }

        if (basemapSelect) {
            basemapSelect.innerHTML = Object.keys(baseMaps).map(name => 
                `<option value="${name}"${name === 'OpenStreetMap' ? ' selected' : ''}>${name}</option>`
            ).join('');
        }

        // Event listener para troca de basemap
        setTimeout(() => {
            const bsSelect = document.getElementById(`${mapId}-basemap-select`);
            if (bsSelect) {
                bsSelect.addEventListener('change', () => {
                    const chosen = baseMaps[bsSelect.value];
                    if (!chosen) return;
                    if (currentBasemap) map.removeLayer(currentBasemap);
                    currentBasemap = chosen;
                    currentBasemap.addTo(map);
                    currentBasemap.bringToBack();
                });
            }
        }, 0);

        const overlayLayers = {
            au: camadas.areasUrbanizadas,
            estadual: camadas.malhaEstadual,
            regioes: camadas.regioes,
            municipios: camadas.municipios,
            malha: camadas.malha,
            vicinais: camadas.malhaVic,
            der: camadas.malhaDER
        };
        
        // Event listeners para checkboxes e ordenação dinâmica por arrastar/soltar
        setTimeout(() => {
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
        
        // Inicializar painéis usando elementos HTML existentes
        createStatsPanel(mapId, overlayLayers, overlayItems, map);
        createLegendPanel(mapId, overlayLayers, overlayItems, map);
        
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
