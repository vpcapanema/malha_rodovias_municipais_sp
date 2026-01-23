// ============================================================
// RESULTADOS - JAVASCRIPT PARA GRÁFICOS (Chart.js)
// ============================================================

// Configurações globais do Chart.js
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
Chart.defaults.font.size = 13;
Chart.defaults.color = '#333';

// Configuração de legenda padrão
const legendConfig = {
    display: true,
    position: 'bottom',
    labels: {
        padding: 15,
        usePointStyle: true,
        font: { size: 12 }
    }
};

// Função para criar gráfico 1: Distribuição por Comprimento de Segmentos
function createChartComprimentoSegmentos() {
    const ctx = document.getElementById('chartComprimentoSegmentos');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['< 0,5 km', '0,5-1 km', '1-2 km', '2-5 km', '5-10 km', '10-20 km', '> 20 km'],
            datasets: [{
                label: 'Quantidade de Segmentos',
                data: [1878, 830, 1091, 1804, 1218, 509, 87],
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                yAxisID: 'y'
            }, {
                label: 'Extensão (km)',
                data: [327, 604, 1596, 5953, 8513, 6815, 2155],
                backgroundColor: 'rgba(255, 159, 64, 0.7)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 2,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            // Evita canvas gigante caso o wrapper não tenha altura fixa
            maintainAspectRatio: true,
            aspectRatio: 2.4,
            resizeDelay: 150,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Distribuição por Comprimento de Segmentos',
                    font: { size: 16, weight: 'bold' }
                },
                legend: legendConfig,
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            if (context.dataset.yAxisID === 'y1') {
                                return label + ': ' + value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' km';
                            }
                            return label + ': ' + value.toLocaleString('pt-BR');
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    title: { display: true, text: 'Quantidade de Segmentos' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    title: { display: true, text: 'Extensão (km)' },
                    grid: { drawOnChartArea: false }
                },
                x: {
                    title: { display: true, text: 'Faixa de Comprimento' }
                }
            }
        }
    });
}

// Função para criar gráfico 2: Tipo Possível de Pavimento
function createChartTipoPavimento() {
    const ctx = document.getElementById('chartTipoPavimento');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [
                'Tipo 9 - Terra/Cascalho (não pavimentado)',
                'Tipo 8 - Asfalto/Pavimentado',
                'Tipo 7 - Outros',
                'Tipo 0 - Não classificado',
                'Tipos 1-2 - Outros'
            ],
            datasets: [{
                data: [16012, 9806, 80, 56, 10],
                backgroundColor: [
                    'rgba(255, 140, 0, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(201, 203, 207, 0.8)',
                    'rgba(153, 102, 255, 0.8)'
                ],
                borderColor: [
                    'rgba(255, 140, 0, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(201, 203, 207, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 60,
                    right: 60,
                    top: 20,
                    bottom: 20
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Distribuição por Tipo Possível de Pavimento (km)',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'bottom',
                    align: 'center',
                    labels: {
                        padding: 15,
                        font: { size: 12 },
                        boxWidth: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return label + ': ' + value.toLocaleString('pt-BR') + ' km (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

// Função para criar gráfico 3: Concentração por Faixas de Extensão
function createChartFaixasExtensao() {
    const ctx = document.getElementById('chartFaixasExtensao');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['0-20 km', '20-40 km', '40-60 km', '60-80 km', '80-100 km', '100-150 km', '150-200 km'],
            datasets: [{
                label: 'Quantidade de Municípios',
                data: [163, 226, 121, 63, 28, 30, 6],
                backgroundColor: [
                    'rgba(255, 107, 107, 0.7)',
                    'rgba(78, 205, 196, 0.7)',
                    'rgba(255, 230, 109, 0.7)',
                    'rgba(168, 230, 207, 0.7)',
                    'rgba(149, 165, 166, 0.7)',
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(155, 89, 182, 0.7)'
                ],
                borderColor: [
                    'rgba(255, 107, 107, 1)',
                    'rgba(78, 205, 196, 1)',
                    'rgba(255, 230, 109, 1)',
                    'rgba(168, 230, 207, 1)',
                    'rgba(149, 165, 166, 1)',
                    'rgba(52, 152, 219, 1)',
                    'rgba(155, 89, 182, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribuição de Municípios por Faixa de Extensão Estimada',
                    font: { size: 16, weight: 'bold' }
                },
                legend: legendConfig,
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const percentages = [25.6, 35.5, 19.0, 9.9, 4.4, 4.7, 0.9];
                            return 'Percentual: ' + percentages[context.dataIndex] + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Quantidade de Municípios' }
                },
                x: {
                    title: { display: true, text: 'Faixa de Extensão' }
                }
            }
        }
    });
}

// Função para criar gráfico 4: Top 10 Municípios com MAIOR Extensão
function createChartTop10Maior() {
    const ctx = document.getElementById('chartTop10Maior');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Cunha', 'Itápolis', 'Araçatuba', 'Morro Agudo', 'Itapetininga', 
                     'Itapeva', 'Campinas', 'Teodoro Sampaio', 'Presidente Epitácio', 'Iguape'],
            datasets: [{
                label: 'Extensão (km)',
                data: [195.02, 181.86, 171.72, 165.05, 159.11, 153.32, 149.80, 142.78, 135.39, 134.54],
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Municípios com Maior Extensão Vicinal Estimada',
                    font: { size: 16, weight: 'bold' }
                },
                legend: legendConfig,
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Extensão: ' + context.parsed.x.toFixed(2) + ' km';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: { display: true, text: 'Extensão (km)' }
                }
            }
        }
    });
}

// Função para criar gráfico 5: Top 10 Municípios com MENOR Extensão
function createChartTop10Menor() {
    const ctx = document.getElementById('chartTop10Menor');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Taquaral', "Guarani d'Oeste", 'Vitória Brasil', 'Santa Lúcia', 'Areiópolis',
                     'Santa Salete', 'Coronel Macedo', 'Carapicuíba', 'Iepê', 'Dolcinópolis'],
            datasets: [{
                label: 'Extensão (km)',
                data: [0.37, 0.97, 1.24, 1.32, 3.20, 3.53, 3.67, 3.70, 4.13, 4.18],
                backgroundColor: 'rgba(231, 76, 60, 0.7)',
                borderColor: 'rgba(231, 76, 60, 1)',
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Municípios com Menor Extensão Vicinal Estimada',
                    font: { size: 16, weight: 'bold' }
                },
                legend: legendConfig,
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Extensão: ' + context.parsed.x.toFixed(2) + ' km';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: { display: true, text: 'Extensão (km)' }
                }
            }
        }
    });
}

// Função para criar gráfico 6: Todas as Regiões Administrativas
async function createChartTop5RA() {
    const ctx = document.getElementById('chartTop5RA');
    if (!ctx) return;

    try {
        // Carregar dados das regiões
        const response = await fetch('../data/regioes_totais.geojson');
        const data = await response.json();
        
        // Extrair e ordenar regiões por extensão
        const regioes = data.features
            .map(f => ({
                nome: f.properties.RA,
                extensao: f.properties.extensao_km || 0
            }))
            .sort((a, b) => b.extensao - a.extensao);
        
        // Preparar labels e dados
        const labels = regioes.map(r => r.nome);
        const valores = regioes.map(r => r.extensao);
        
        // Gerar cores dinâmicas (gradiente de azul para cinza)
        const cores = valores.map((v, i) => {
            const ratio = i / (valores.length - 1);
            const r = Math.round(52 + ratio * (149 - 52));   // 52 -> 149
            const g = Math.round(152 + ratio * (165 - 152)); // 152 -> 165
            const b = Math.round(219 + ratio * (166 - 219)); // 219 -> 166
            return `rgba(${r}, ${g}, ${b}, 0.7)`;
        });
        
        const coresBorda = valores.map((v, i) => {
            const ratio = i / (valores.length - 1);
            const r = Math.round(52 + ratio * (149 - 52));
            const g = Math.round(152 + ratio * (165 - 152));
            const b = Math.round(219 + ratio * (166 - 219));
            return `rgba(${r}, ${g}, ${b}, 1)`;
        });

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Extensão Total (km)',
                    data: valores,
                    backgroundColor: cores,
                    borderColor: coresBorda,
                    borderWidth: 2
                }]
            },
            options: {
                indexAxis: 'y', // Gráfico horizontal para melhor visualização
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Regiões Administrativas por Extensão Vicinal Estimada',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.x;
                                const total = valores.reduce((a, b) => a + b, 0);
                                const percent = ((value / total) * 100).toFixed(1);
                                return [
                                    'Extensão: ' + value.toLocaleString('pt-BR', {maximumFractionDigits: 2}) + ' km',
                                    'Percentual do total: ' + percent + '%'
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: { display: true, text: 'Extensão Total (km)' }
                    },
                    y: {
                        title: { display: true, text: 'Região Administrativa' }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Erro ao carregar dados das regiões:', error);
    }
}

// Inicializar todos os gráficos quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    createChartComprimentoSegmentos();
    createChartTipoPavimento();
    createChartFaixasExtensao();
    createChartTop10Maior();
    createChartTop10Menor();
    createChartTop5RA();
});
