# 🗺️ Como Adicionar os Mapas Temáticos

## Situação Atual

A página `pages/mapas.html` contém **4 placeholders de mapas** com instruções detalhadas de como gerá-los no QGIS. Atualmente são exibidos boxes informativos no lugar das visualizações.

## Passos para Gerar e Adicionar os Mapas

### 1️⃣ Arquivo de Dados

Os mapas são gerados a partir do arquivo:
```
resultados/dados_processados/malha_municipal_sp.gpkg
```

Este arquivo deve conter os seguintes campos:
- `densidade_km_10000km2` - Densidade territorial
- `densidade_km_10000hab` - Densidade per capita
- `razao_osm_der` - Razão OSM/DER
- `regiao_administrativa` - Região administrativa (16 RAs)

### 2️⃣ Gerar Mapas no QGIS

#### Método Automático (Script Python)
```bash
python app_web/gerar_mapas_qgis.py
```
**Nota:** O script atual fornece instruções. Para automação completa, implemente com PyQGIS.

#### Método Manual

Abra o QGIS e siga as instruções abaixo para cada mapa:

---

### 🗺️ **Mapa 1: Densidade Territorial**

**Arquivo de saída:** `app_web/images/mapa1_densidade_territorial.png`

1. Carregar `malha_municipal_sp.gpkg` no QGIS
2. Propriedades da Camada → Simbologia → **Graduado**
3. Campo: `densidade_km_10000km2`
4. Modo: **Quebras Naturais (Jenks)**
5. Classes: **5**
6. Rampa de cor: **Reds** (vermelho crescente)
7. Layout → Exportar como imagem PNG (1920x1080px)

**Legenda:**
- Muito Alta: > 8.000 km/10.000km²
- Alta: 5.000 - 8.000
- Média: 3.000 - 5.000
- Baixa: 1.500 - 3.000
- Muito Baixa: < 1.500

---

### 👥 **Mapa 2: Densidade per Capita**

**Arquivo de saída:** `app_web/images/mapa2_densidade_per_capita.png`

1. Campo: `densidade_km_10000hab`
2. Modo: **Quantis**
3. Classes: **5**
4. Rampa de cor: **Oranges** (laranja crescente)
5. Adicionar rótulos para municípios com densidade > 20 km/10.000 hab
6. Exportar PNG (1920x1080px)

---

### ⚖️ **Mapa 3: Razão OSM/DER**

**Arquivo de saída:** `app_web/images/mapa3_razao_osm_der.png`

1. Campo: `razao_osm_der`
2. Modo: **Quebras Manuais**
3. Classes:
   - < 2x (convergência)
   - 2x - 5x (divergência moderada)
   - 5x - 10x (divergência alta)
   - 10x - 15x (divergência muito alta)
   - > 15x (divergência crítica)
4. Rampa de cor: **RdYlGn invertida** (vermelho = alta divergência)
5. Adicionar camada `rede_der.gpkg` como linhas cinzas (referência)
6. Exportar PNG (1920x1080px)

---

### 🏛️ **Mapa 4: Regiões Administrativas**

**Arquivo de saída:** `app_web/images/mapa4_regioes_administrativas.png`

1. Processar → Dissolver → Campo: `regiao_administrativa`
2. Calcular densidade agregada por RA (soma OSM_km / soma área_km2)
3. Simbologia: **Diagrama de barras** ou **Círculos proporcionais**
4. Paleta: **Spectral** (16 cores distintas)
5. Rótulos: Nome da RA + densidade total
6. Exportar PNG (1920x1080px)

---

### 3️⃣ Substituir Placeholders por Imagens Reais

Após gerar os 4 mapas, edite `pages/mapas.html` e substitua os blocos de placeholder por tags `<img>`:

**Exemplo para Mapa 1:**

Substitua:
```html
<div class="card-content" style="text-align: center; padding: 2rem; background: #f8f9fa;">
    <div style="border: 2px dashed #0066cc; padding: 3rem; ...">
        <!-- Placeholder content -->
    </div>
</div>
```

Por:
```html
<div class="card-content">
    <img src="../images/mapa1_densidade_territorial.png" 
         alt="Mapa de Densidade Territorial OSM" 
         style="width: 100%; height: auto; border-radius: 8px;">
    <p style="text-align: center; color: #666; margin-top: 1rem; font-size: 0.9rem;">
        Figura 1: Densidade de vicinais por município (km/10.000km²)
    </p>
</div>
```

Repita para os 4 mapas.

---

## 4️⃣ Estrutura Final Esperada

```
app_web/
├── images/
│   ├── mapa1_densidade_territorial.png    (1920x1080)
│   ├── mapa2_densidade_per_capita.png     (1920x1080)
│   ├── mapa3_razao_osm_der.png            (1920x1080)
│   └── mapa4_regioes_administrativas.png  (1920x1080)
├── pages/
│   └── mapas.html (atualizado com tags <img>)
└── gerar_mapas_qgis.py
```

---

## ℹ️ Informações Técnicas

- **Formato:** PNG (melhor qualidade para mapas)
- **Resolução:** 1920x1080px (Full HD)
- **Sistema de Coordenadas:** EPSG:31983 (SIRGAS 2000 / UTM 23S) ou EPSG:4326 (WGS 84)
- **Cores:** Paletas ColorBrewer (acessibilidade para daltônicos)
- **Fonte:** Arial ou Liberation Sans (legibilidade)

---

## 🚀 Próximos Passos

1. ✅ Executar processamento completo dos dados
2. ⏳ Gerar os 4 mapas no QGIS (manual ou automatizado)
3. ⏳ Substituir placeholders em `mapas.html`
4. ✅ Validar visualização no navegador
5. ⏳ Adicionar mapas interativos (opcional: Leaflet.js)

---

## 📚 Referências

- [QGIS Documentation](https://docs.qgis.org/)
- [PyQGIS Cookbook](https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/)
- [ColorBrewer](https://colorbrewer2.org/) - Paletas de cores para mapas
