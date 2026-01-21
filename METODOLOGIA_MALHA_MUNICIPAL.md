# Metodologia para Estimativa da Malha Viária Municipal do Estado de São Paulo

## 1. Contexto e Objetivo

**Objetivo:** Extrair da base OSM (`base_linhas.gpkg`) apenas as vias de responsabilidade municipal, excluindo:
- Rodovias **federais** (BR-xxx)
- Rodovias **estaduais** (SP-xxx)
- Vias **urbanas** (ruas, avenidas, travessas, etc. - responsabilidade das prefeituras)

O resultado será a **malha viária municipal rural** (estradas vicinais/municipais).

---

## 2. Análise da Base de Dados

### 2.1 Visão Geral
| Característica | Valor |
|----------------|-------|
| Total de registros | 804.868 |
| CRS | EPSG:4326 |
| Cobertura | Estado de São Paulo |

### 2.2 Classificação Highway (OSM)

| Tipo | Quantidade | % | Descrição |
|------|-----------|---|-----------|
| residential | 477.550 | 59,3% | Vias residenciais urbanas |
| unclassified | 82.917 | 10,3% | Vias não classificadas (potenciais vicinais) |
| service | 81.472 | 10,1% | Vias de serviço/acesso |
| tertiary | 50.292 | 6,2% | Vias terciárias |
| secondary | 37.452 | 4,7% | Vias secundárias |
| primary | 19.964 | 2,5% | Vias primárias |
| motorway + link | 20.520 | 2,5% | Rodovias expressas (autoestradas) |
| trunk + link | 11.501 | 1,4% | Rodovias principais |
| tertiary_link | 3.088 | 0,4% | Links terciários |
| living_street | 6.959 | 0,9% | Zonas de tráfego calmo |
| outras | ~13.000 | 1,6% | Outras classificações |

### 2.3 Referências de Rodovias (coluna `ref`)

| Tipo | Quantidade |
|------|-----------|
| Total com ref | 35.326 (4,4%) |
| Com BR-xxx | 8.747 |
| Com SP-xxx | 24.753 |
| Outros códigos | 9.390 |

**Observação importante:** Os códigos como `SPA-xxx`, `SPI-xxx`, `SPM-xxx` são códigos de **estradas municipais** e devem ser MANTIDOS.

### 2.4 Padrões de Nomes para Vias Urbanas

| Padrão | Quantidade | Classificação |
|--------|-----------|---------------|
| Rua | 364.280 | URBANA - EXCLUIR |
| Avenida | 67.607 | URBANA - EXCLUIR |
| Travessa | 10.823 | URBANA - EXCLUIR |
| Alameda | 9.887 | URBANA - EXCLUIR |
| Praça | 5.327 | URBANA - EXCLUIR |
| Viela | 2.955 | URBANA - EXCLUIR |
| Largo | 287 | URBANA - EXCLUIR |
| Beco | 102 | URBANA - EXCLUIR |
| **Estrada** | 16.780 | **MANTER** (potencial vicinal) |
| **Rodovia** | 23.593 | ANALISAR (pode ser BR/SP) |
| **Vicinal** | 2.643 | **MANTER** |

---

## 3. Metodologia Proposta (3 Etapas)

### ETAPA 1: Exclusão por Classificação Highway (mais simples e impactante)

**Excluir imediatamente:**
```
highway IN ('motorway', 'motorway_link', 'trunk', 'trunk_link')
```
> Isso remove ~32.000 segmentos de rodovias expressas e principais

**Excluir vias urbanas:**
```
highway IN ('residential', 'living_street', 'service')
```
> Isso remove ~565.000 segmentos de vias tipicamente urbanas

### ETAPA 2: Exclusão por Referência de Rodovia

**Excluir vias com referência federal ou estadual:**
```
ref CONTAINS 'BR-' OR ref CONTAINS 'SP-'
```
> Isso remove rodovias federais e estaduais dos tipos restantes

**MANTER códigos municipais:**
- `SPA-xxx` (Estrada Vicinal Acesso)
- `SPI-xxx` (Estrada Vicinal Interna)
- `SPM-xxx` (Estrada Municipal)
- Códigos de 3 letras municipais (ex: UCH-050, MAS-17, RG-01)

### ETAPA 3: Exclusão Espacial por Área Urbana IBGE

Usar o arquivo `au_ibge.gpkg` (128.459 polígonos de áreas urbanas) para:
- Remover vias que estão **inteiramente dentro** de áreas urbanas
- OU remover vias que têm **mais de X%** do comprimento dentro de AU

---

## 4. Critérios de Seleção Final

### Tipos de Highway a MANTER (candidatos a malha municipal):
| Highway | Ação | Justificativa |
|---------|------|---------------|
| unclassified | MANTER | Principal fonte de estradas vicinais |
| tertiary | MANTER (filtrar) | Vias terciárias rurais |
| secondary | MANTER (filtrar) | Algumas são municipais |
| primary | MANTER (filtrar) | Algumas são municipais sem ref |
| track | MANTER | Estradas de terra/agrícolas |

### Tipos de Highway a EXCLUIR:
| Highway | Ação | Justificativa |
|---------|------|---------------|
| motorway, motorway_link | EXCLUIR | Autoestradas (estaduais/federais) |
| trunk, trunk_link | EXCLUIR | Rodovias principais (estaduais/federais) |
| residential | EXCLUIR | Ruas residenciais urbanas |
| living_street | EXCLUIR | Zonas de tráfego urbano |
| service | EXCLUIR | Vias de serviço urbano |
| primary_link, secondary_link | ANALISAR | Links de acesso |
| tertiary_link | ANALISAR | Links terciários |

---

## 5. Fluxo de Processamento Recomendado

```
┌─────────────────────────────────────────────────────────┐
│              BASE OSM (804.868 registros)               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ ETAPA 1: Filtro por Highway                             │
│ Excluir: motorway*, trunk*, residential, living_street, │
│          service                                         │
│ Estimativa: ~210.000 registros restantes                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ ETAPA 2: Filtro por Referência                          │
│ Excluir: ref LIKE '%BR-%' OR ref LIKE '%SP-%'           │
│ (exceto códigos municipais SPA, SPI, SPM)               │
│ Estimativa: ~180.000 registros restantes                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ ETAPA 3: Filtro por Nomes Urbanos                       │
│ Excluir: name LIKE 'Rua %', 'Avenida %', 'Travessa %',  │
│          'Alameda %', 'Praça %', 'Viela %', 'Largo %',  │
│          'Beco %'                                        │
│ Estimativa: ~50.000-80.000 registros restantes          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ ETAPA 4: Filtro Espacial (Opcional)                     │
│ Excluir: vias dentro de AU IBGE                         │
│ Usar au_ibge.gpkg (128.459 polígonos)                   │
│ Estimativa: ~30.000-50.000 registros finais             │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│           MALHA VIÁRIA MUNICIPAL ESTIMADA               │
│              (Estradas Vicinais SP)                     │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Resultados do Processamento

| Etapa | Registros | % Total | Extensão (km) |
|-------|-----------|---------|---------------|
| Base original | 804.868 | 100,0% | - |
| Após Etapa 1 (highway) | 206.866 | 25,7% | - |
| Após Etapa 2 (ref BR/SP) | 195.775 | 24,3% | - |
| Após Etapa 3 (nomes urbanos) | 123.950 | 15,4% | 126.177 km |
| **Após Etapa 4 (AU IBGE)** | **100.879** | **12,5%** | **124.098 km** |

### Distribuição Final por Tipo de Highway

| Highway | Quantidade | % |
|---------|-----------|---|
| unclassified | 72.975 | 72,3% |
| tertiary | 13.157 | 13,0% |
| secondary | 8.246 | 8,2% |
| primary_link | 2.464 | 2,4% |
| secondary_link | 1.782 | 1,8% |
| primary | 1.569 | 1,6% |
| tertiary_link | 686 | 0,7% |

---

## 7. Considerações Importantes

### 7.1 Vantagens desta Metodologia
- ✅ Ágil: usa apenas atributos, sem processamento espacial pesado
- ✅ Replicável: critérios objetivos e documentados
- ✅ Escalável: pode ser aplicada a outros estados
- ✅ Validável: cada etapa pode ser auditada

### 7.2 Limitações
- ⚠️ Depende da qualidade dos dados OSM
- ⚠️ Algumas vias podem estar mal classificadas
- ⚠️ Nomes em português podem ter variações

### 7.3 Validação Recomendada
1. Amostragem visual em QGIS
2. Comparação com base do DER-SP (se disponível)
3. Verificação de conectividade da rede

---

## 8. Arquivos Gerados

| Arquivo | Descrição | Registros | Extensão |
|---------|-----------|-----------|----------|
| `malha_municipal_sp.gpkg` | Malha municipal (sem AU) | 123.950 | 126.177 km |
| `malha_municipal_sp_sem_au.gpkg` | Malha municipal + filtro espacial AU IBGE | 100.879 | 124.098 km |

## 9. Próximos Passos

1. [x] Implementar script Python com as 4 etapas
2. [x] Gerar estatísticas de cada etapa
3. [ ] Validar amostra visualmente no QGIS
4. [ ] Ajustar critérios se necessário
5. [x] Exportar malha final

---

**Autor:** Análise automatizada
**Data:** Janeiro/2026
**Versão:** 1.0
