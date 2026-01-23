const fullscreenMapDefinitions = {
    'malha-completa': {
        title: 'Malha Vicinal Estimada de São Paulo',
        description: 'Todas as camadas (municípios, malha OSM e DER) exibidas com possibilidade de alternar as camadas principais.',
        create: ({ municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel }) => {
            criarMapaMalhaCompleta(municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel);
        }
    },
    pavimento: {
        title: 'Distribuição por Tipo de Pavimento',
        description: 'Agrupa segmentos OSM e tiles da malha total por tipo de superfície para mostrar a cobertura Pavimentado vs. Terra/Cascalho.',
        create: ({ municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel }) => {
            criarMapaVicinaisPorTipo('mapaFullscreen', municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel);
        }
    },
    'ranking-extensao': {
        title: 'Extensão Total da Malha Vicinal por Município',
        description: 'Gradiente contínuo com toggle OSM / Total para o ranking municipal de extensão.',
        create: ({ municipiosGeo, boundsSP }) => {
            criarMapaRankingExtensao('mapaFullscreen', municipiosGeo, boundsSP);
        }
    },
    'densidade-area': {
        title: 'Densidade por Área Territorial (km/10.000km²)',
        description: 'Gradiente contínuo mostrando a relação entre extensão e área municipal.',
        create: ({ municipiosGeo, boundsSP }) => {
            criarMapaDensidadeArea('mapaFullscreen', municipiosGeo, boundsSP);
        }
    },
    'densidade-pop': {
        title: 'Densidade por População (km/10.000 habitantes)',
        description: 'Gradiente contínuo ilustrando quantos km de vicinais existem para cada 10.000 habitantes.',
        create: ({ municipiosGeo, boundsSP }) => {
            criarMapaDensidadePop('mapaFullscreen', municipiosGeo, boundsSP);
        }
    },
    'disparidade-area': {
        title: 'Disparidades Espaciais na Densidade',
        description: 'Classes de desvio em relação à média estadual (Muito Abaixo a Muito Acima).',
        create: ({ municipiosGeo, boundsSP }) => {
            criarMapaDisparidades('mapaFullscreen', municipiosGeo, 'classe_disp_area', boundsSP);
        }
    },
    'disparidade-pop': {
        title: 'Disparidades Populacionais na Densidade',
        description: 'Classes de desvio populacional com toggle OSM / Total (MAD).',
        create: ({ municipiosGeo, boundsSP }) => {
            criarMapaDisparidades('mapaFullscreen', municipiosGeo, 'classe_disp_pop', boundsSP);
        }
    }
};

const getFullscreenStatusEl = () => document.getElementById('fullscreenStatus');
const setFullscreenStatus = (mensagem) => {
    const fullscreenStatusEl = getFullscreenStatusEl();
    if (fullscreenStatusEl) {
        fullscreenStatusEl.textContent = mensagem;
    }
};

async function carregarDadosFullscreen() {
    setFullscreenStatus('Carregando municípios...');
    const respMun = await fetch('../data/municipios_completo.geojson');
    if (!respMun.ok) {
        throw new Error('Não foi possível carregar municipios_completo.geojson');
    }
    const municipiosGeo = await respMun.json();
    const boundsSP = L.geoJSON(municipiosGeo).getBounds();

    setFullscreenStatus('Carregando malha vicinal estimada...');
    let malhaVicinaisGeo = null;
    try {
        const respVicinais = await fetch('../data/malha_vicinal_estimada_osm.geojson');
        if (respVicinais.ok) {
            malhaVicinaisGeo = await respVicinais.json();
        } else {
            console.warn('Não foi possível carregar malha_vicinal_estimada_osm.geojson (HTTP ' + respVicinais.status + ')');
        }
    } catch (err) {
        console.warn('Erro ao carregar malha_vicinal_estimada_osm.geojson', err);
    }

    setFullscreenStatus('Carregando metadados da Malha Total...');
    let malhaTotalTilesDisponivel = false;
    try {
        const respTiles = await fetch('../data/malha_total_tiles/metadata.json');
        if (respTiles.ok) {
            const infoTiles = await respTiles.json();
            malhaTotalTilesDisponivel = Boolean(infoTiles?.tileUrlTemplate || (Array.isArray(infoTiles?.tiles) && infoTiles.tiles.length));
        }
    } catch (err) {
        console.warn('Erro ao carregar metadata da malha total', err);
    }

    try {
        const respSegmentos = await fetch('../data/segmentos_estatisticas.json');
        if (respSegmentos.ok) {
            window.dadosSegmentos = await respSegmentos.json();
        }
    } catch (err) {
        console.warn('Erro ao carregar segmentos_estatisticas.json', err);
    }

    setFullscreenStatus('Dados carregados com sucesso. Preparando mapa...');
    return { municipiosGeo, malhaVicinaisGeo, boundsSP, malhaTotalTilesDisponivel };
}

function extrairConfiguracao() {
    const params = new URLSearchParams(window.location.search);
    const chave = (params.get('map') || 'ranking-extensao').toLowerCase();
    return fullscreenMapDefinitions[chave] || fullscreenMapDefinitions['ranking-extensao'];
}

document.addEventListener('DOMContentLoaded', async () => {
    const config = extrairConfiguracao();
    const titleEl = document.getElementById('fullscreenTitle');
    const descEl = document.getElementById('fullscreenDescription');
    if (titleEl) titleEl.textContent = config.title;
    if (descEl) descEl.textContent = config.description;
    document.title = `${config.title} | Tela cheia`;

    try {
        const dados = await carregarDadosFullscreen();
        setFullscreenStatus('Gerando o mapa...');
        config.create(dados);
        setFullscreenStatus('Mapa pronto!');
    } catch (error) {
        console.error('Erro ao gerar mapa fullscreen', error);
        setFullscreenStatus('Erro ao carregar os dados. Veja o console do navegador.');
    }
});