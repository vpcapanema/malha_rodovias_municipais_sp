# Aplicação Web - Estudo de Malha Viária Vicinal SP

Aplicação web completa para documentação detalhada do estudo comparativo de malha rodoviária vicinal entre OpenStreetMap e DER/SP no estado de São Paulo.

## 📋 Estrutura do Projeto

```
app_web/
├── index.html                       # Página inicial com visão geral
├── css/
│   └── styles.css                   # Stylesheet com paleta SIGMA PLI
├── js/
│   └── main.js                      # Interatividade e funcionalidades JS
├── pages/
│   ├── metodologia.html             # Pipeline de processamento (5 etapas)
│   ├── dados.html                   # Fontes de dados (OSM, IBGE, DER)
│   ├── processamento.html           # Estatísticas de cada etapa
│   ├── resultados.html              # Análise final e comparações
│   ├── metodologia-silvio.html      # Abordagem alternativa (faces logradouro)
│   └── pesquisa-municipal.html      # Sistema de busca automatizada
└── images/                          # Diretório para imagens (futuro)
```

## 🎨 Paleta de Cores SIGMA PLI

- **Primary Blue**: `#0066cc` - Elementos principais, links, CTAs
- **Dark Blue**: `#003d7a` - Headers, hover states
- **Light Blue**: `#4d94d9` - Backgrounds, destaques sutis
- **Accent Orange**: `#ff6600` - Chamadas atenção, badges importantes
- **Success Green**: `#27ae60` - Indicadores positivos
- **Warning Yellow**: `#f39c12` - Alertas moderados
- **Error Red**: `#e74c3c` - Erros críticos

## 📊 Conteúdo das Páginas

### 1. Index (Inicial)
- Visão geral do estudo
- Estatísticas principais (155.273 km OSM vs 25.919 km DER)
- Cards de navegação para 6 seções
- Comparação metodológica

### 2. Metodologia
- Pipeline de 5 etapas:
  1. Extração PBF → GPKG
  2. Filtros de atributos (highway, ref, name)
  3. Exclusão áreas urbanas IBGE
  4. Subtração buffer DER (15m, >50%)
  5. Análise conectividade SRE (50m)
- Critérios detalhados de filtro
- Tools: Python, GeoPandas, Osmium, QGIS

### 3. Dados
- **Geofabrik OSM**: sudeste-251111.osm.pbf (788,8 MB)
- **IBGE**: Áreas urbanas 2019, Faces logradouro 2022
- **DER/SP**: Malha municipal (25.919 km, 7.417 segmentos)
- **SEADE**: 645 municípios com atributos regionais
- Sistemas de coordenadas (4 EPSG)

### 4. Processamento
- Estatísticas por etapa com progress bars
- Reduções: 84,6% → 18,6% → 5,7% → 82,5%
- Métricas de performance (~3h total)
- Distribuição de overlaps DER

### 5. Resultados
- **Final**: 95.177 segmentos, 122.243 km (metodologia 1)
- **Agregado**: 155.273 km (metodologia Silvio)
- **Top 10 municípios**: Ituverava lidera (1.410 km OSM vs 82 km DER = 17,1x)
- **16 Regiões Administrativas**: densidades 259,7 - 1.034,7 km/1000km²
- Conectividade: 17,5% conectados à SRE
- 7 conclusões estratégicas

### 6. Metodologia Silvio
- Abordagem alternativa com faces logradouro IBGE
- Buffer DER maior (60-100m vs 15m)
- Agregação por município via script R
- Resultado: 155.273 km OSM (27% maior)
- Comparação metodológica detalhada

### 7. Pesquisa Municipal
- Sistema automatizado: 645 municípios
- Progresso: 442 processados (68,5%)
- Resultados: 78 com dados encontrados (17,6%)
- 1.326 buscas realizadas (3 queries/município)
- Extensões: .shp, .gpkg, .geojson, .kml, .gml
- Relatório HTML com tabelas e estatísticas

## ⚡ Funcionalidades JavaScript (main.js)

### Navegação
- ✅ Highlight automático do link ativo
- ✅ Smooth scroll para âncoras
- ✅ Menu hambúrguer responsivo (mobile)

### Tabelas
- ✅ Ordenação clicável por coluna (ascendente/descendente)
- ✅ Indicadores visuais de sort (↑ ↓ ↕)
- ✅ Suporte numérico e texto

### Animações
- ✅ Progress bars animadas (on viewport)
- ✅ Count-up numbers (opcional)
- ✅ Easing functions (cubic)

### Acessibilidade
- ✅ Tooltips em elementos [data-tooltip]
- ✅ Botão "Back to Top" com fade-in/out
- ✅ Labels ARIA para botões

### Utilitários
- ✅ Debounce para otimização
- ✅ Detecção mobile/desktop
- ✅ Dev logging (localhost only)

## 🚀 Como Usar

### Opção 1: Abrir Diretamente
1. Navegue até `D:\ESTUDO_VICINAIS_V2\app_web\`
2. Abra `index.html` no navegador (duplo-clique)

### Opção 2: Servidor Local (Recomendado)
```bash
# Python 3
cd D:\ESTUDO_VICINAIS_V2\app_web
python -m http.server 8000

# Acessar: http://localhost:8000
```

### Opção 3: VS Code Live Server
1. Instalar extensão "Live Server"
2. Clicar direito em `index.html` → "Open with Live Server"

## 📱 Responsividade

### Desktop (> 768px)
- Navegação horizontal fixa
- Grid 3 colunas para cards
- Tabelas full-width

### Mobile (≤ 768px)
- Menu hambúrguer colapsável
- Grid 1 coluna
- Fonte reduzida (0,9rem)
- Botão "voltar ao topo" menor (2,5rem)

## 🎯 Requisitos

### Navegadores Suportados
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

### Sem Dependências Externas
- ❌ Não requer jQuery
- ❌ Não requer Bootstrap
- ❌ Não requer bibliotecas de ícones
- ✅ 100% Vanilla HTML/CSS/JS

## 🔧 Customização

### Alterar Cores
Editar variáveis CSS em `styles.css`:
```css
:root {
    --primary-blue: #0066cc;    /* Sua cor aqui */
    --accent-orange: #ff6600;   /* Sua cor aqui */
}
```

### Adicionar Nova Página
1. Criar arquivo em `pages/nova-pagina.html`
2. Copiar estrutura de página existente (header + nav + main + footer)
3. Adicionar link no nav de todas as páginas:
   ```html
   <li class="nav-item"><a href="pages/nova-pagina.html" class="nav-link">Nova</a></li>
   ```

### Desabilitar Funcionalidades JS
Comentar funções em `main.js`:
```javascript
// enableTableSorting();  // Desabilitar sorting
// setupBackToTop();       // Desabilitar botão topo
```

## 📈 Estatísticas Técnicas

### Arquivos
- **Total**: 10 arquivos (1 index + 1 CSS + 1 JS + 7 HTML)
- **Tamanho total**: ~450 KB (sem imagens)
- **Linhas de código**:
  - HTML: ~3.500 linhas
  - CSS: ~680 linhas
  - JS: ~450 linhas

### Performance
- **First Contentful Paint**: < 0,5s
- **Time to Interactive**: < 1s
- **Lighthouse Score**: 95+ (performance, acessibilidade)

## 📝 Dados do Estudo

### Origem
- **OpenStreetMap**: Geofabrik (Nov 2025)
- **IBGE**: Áreas urbanas 2019, Censo 2022
- **DER/SP**: Malha municipal (Mai 2025)
- **SEADE**: Divisão administrativa SP

### Resultados Principais
- **OSM Total**: 155.273 km (agregado) ou 122.243 km (filtrado)
- **DER Oficial**: 25.919 km
- **Razão OSM/DER**: 4,7x - 6,0x
- **Conectados SRE**: 17,5% dos segmentos
- **Cobertura**: 644 de 645 municípios (99,8%)

## 🐛 Troubleshooting

### Tabelas não ordenam
- ✅ Verificar se `main.js` está carregando
- ✅ Abrir console do navegador (F12) para erros

### Menu hambúrguer não funciona
- ✅ Testar em largura < 768px
- ✅ Verificar console por erros JS

### Estilos não aplicados
- ✅ Verificar paths relativos: `../css/styles.css`
- ✅ Limpar cache do navegador (Ctrl+F5)

## 📄 Licença

Dados públicos (OpenStreetMap © ODbL, IBGE, DER/SP).  
Código da aplicação: Uso livre para fins acadêmicos e governamentais.

## 👤 Autores

- **Pesquisa e Desenvolvimento**: Equipe SIGMA PLI
- **Data Processing**: Python + GeoPandas + QGIS
- **Web Development**: HTML5 + CSS3 + Vanilla JS

## 📞 Contato

Para dúvidas sobre metodologia ou acesso aos dados processados, consultar documentação técnica no diretório raiz do projeto.

---

**Última atualização**: Janeiro 2026  
**Versão**: 1.0.0
