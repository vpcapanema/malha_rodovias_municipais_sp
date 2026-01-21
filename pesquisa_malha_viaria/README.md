# 🔍 Pesquisa Sistematizada - Malha Viária Municipal São Paulo

## 📋 Objetivo

Pesquisa sistematizada e estruturada em **TODOS os 645 municípios** de São Paulo em busca de bases de dados oficiais (preferencialmente vetoriais) da malha viária municipal.

## 📊 Status Atual

- **Municípios Pesquisados**: 50/645 (7.8%)
- **Taxa de Sucesso de Acessos**: 8.7%
- **Municípios com Dados Encontrados**: 5
- **Total de Buscas Realizadas**: 150
- **Arquivos de Progresso**: `pesquisa_dados/progresso/progresso.json`

## 📁 Estrutura de Diretórios

```
pesquisa_malha_viaria/
├── EXECUTE_PESQUISA.py                 # Script de execução (primeiros 400 munis)
├── PESQUISA_COMPLETA_645.py            # Script principal (TODOS os 645 munis)
├── gerar_relatorio_atual.py             # Gera relatório HTML atualizado
├── monitorar_progresso.py              # Monitora progresso em tempo real
├── lista_645_municipios.py             # Lista dos 645 municípios
├── municipios_645_final.json           # JSON com lista completa
├── pesquisa_dados/
│   ├── progresso/
│   │   └── progresso.json              # Arquivo de progresso (atualizado a cada 10 munis)
│   ├── relatorios/
│   │   ├── diagnostico_ATUAL.html      # Relatório HTML atual
│   │   └── diagnostico_*.html          # Histórico de relatórios
│   ├── dados_encontrados/              # Dados baixados serão organizados aqui
│   ├── logs/                           # Logs de execução
│   └── README.md                       # Esta documentação
```

## 🚀 Como Executar

### 1. Executar Pesquisa Completa (Recomendado)

```bash
cd D:\ESTUDO_VICINAIS_V2\pesquisa_malha_viaria
python PESQUISA_COMPLETA_645.py
```

**Recursos:**
- ✓ Pesquisa TODOS os 645 municípios
- ✓ Salva progresso a cada 10 municípios
- ✓ Retoma automaticamente se interrompido
- ✓ Gera relatório HTML final
- ✓ Tempo estimado: ~20-30 minutos

### 2. Monitorar Progresso (em outro terminal)

```bash
cd D:\ESTUDO_VICINAIS_V2\pesquisa_malha_viaria
python monitorar_progresso.py
```

### 3. Gerar Relatório Atualizado

```bash
cd D:\ESTUDO_VICINAIS_V2\pesquisa_malha_viaria
python gerar_relatorio_atual.py
```

## 📈 Metodologia de Busca

Para cada município, o script busca em:

1. **Site Oficial**: `https://{municipio}.sp.gov.br`
2. **Portal de Dados**: `https://{municipio}.sp.gov.br/dados`
3. **Secretaria de Obras**: `https://{municipio}.sp.gov.br/secretaria-de-obras`

### Termos Buscados

- Malha viária / rede viária
- Shapefile / GeoJSON / GeoPackage
- Cartografia / dados geográficos
- SIG / GIS
- Dados abertos

## 📊 Saídas Esperadas

### 1. Arquivo de Progresso
`pesquisa_dados/progresso/progresso.json`

Contém:
- Estatísticas gerais
- Detalhes de cada município pesquisado
- URLs testadas
- Dados encontrados

### 2. Relatórios HTML

- `diagnostico_ATUAL.html` - Relatório em tempo real com progresso
- `diagnostico_*.html` - Histórico de relatórios anteriores

Mostra:
- Total de municípios pesquisados
- Taxa de sucesso/falha de acessos
- % de municípios com dados
- Detalhes por município
- Visualização em gráficos

### 3. Dados Encontrados

Organizados em: `pesquisa_dados/dados_encontrados/{municipio}/`

Estrutura por município:
- Arquivos baixados
- Links encontrados
- Descrição do tipo de dado

## 🎯 Características Implementadas

✅ **Pesquisa Sistemática**
- 3 URLs por município (site oficial, portal dados, secretaria obras)
- Timeout configurável
- Retry automático

✅ **Gestão de Progresso**
- Salvamento incremental a cada 10 municípios
- Retoma automática se interrompido
- Rastreamento detalhado

✅ **Análise e Relatórios**
- Cálculo de taxas de sucesso/falha
- Relatório HTML interativo
- Dashboard com gráficos de progresso

✅ **Organização de Dados**
- Estrutura de diretórios por município
- Metadados salvos em JSON
- Fácil acesso aos resultados

## 📝 Exemplo de Saída

```
╔════════════════════════════════════════════════════════════════╗
║   PESQUISA COMPLETA - TODOS OS 645 MUNICÍPIOS DE SÃO PAULO   ║
║                    Versão com Progresso                       ║
╚════════════════════════════════════════════════════════════════╝

Municípios a pesquisar: 645
Início: 12:06:23

[  1/645] ✗ Aparecida d'Oeste
[  2/645] ✗ Caçadore
[  3/645] ✗ Maripenga
...
[ 10/645] ✗ Janetão          | Sucesso: 8.7%
...
[645/645] ✓ Município Final  | Sucesso: XX.X%

╔════════════════════════════════════════════════════════════════╗
║                    PESQUISA FINALIZADA!                       ║
╚════════════════════════════════════════════════════════════════╝

✓ Municípios pesquisados: 645
✓ Total de buscas: 1935
✓ Acessos bem-sucedidos: 234
✓ Dados encontrados em: 56 municípios

Relatório HTML: pesquisa_dados/relatorios/diagnostico_*.html
Progresso salvo em: pesquisa_dados/progresso/progresso.json
```

## 🔍 Interpretando Resultados

### ✓ (Acessado)
Site do município foi acessado com sucesso

### ✗ (Não Acessado)
Site não foi localizado ou está indisponível

### Dados Encontrados
Quando no relatório aparece "Municípios com Dados Encontrados", significa:
- Site foi acessado
- Contém referência a termos relacionados a malha viária
- Potencial para ter dados disponíveis

## 📂 Próximos Passos (Manual)

Após conclusão da pesquisa:

1. **Revisar Relatório HTML**
   - Identificar municípios com maior probabilidade de ter dados
   - Registrar URLs encontradas

2. **Acessar Manualmente Municípios com Dados**
   - Verificar links encontrados
   - Baixar bases de dados disponíveis

3. **Organizar Dados por Região**
   - Agrupar por região metropolitana
   - Agrupar por bacia hidrográfica
   - Categorizar por tipo de dado

## 🛠️ Troubleshooting

### Pesquisa Interrompida
- Execute novamente `PESQUISA_COMPLETA_645.py`
- Script retomará de onde parou usando `progresso.json`

### Relatório não Atualiza
- Execute: `python gerar_relatorio_atual.py`
- Verifique arquivo JSON: `pesquisa_dados/progresso/progresso.json`

### Timeout em Conexões
- Ajuste `timeout=5` em `PESQUISA_COMPLETA_645.py`
- Aumente para `timeout=10` se necessário

## 📞 Informações Adicionais

**Bases de Referência Conhecidas:**
- IBGE - Malha Municipal
- OpenStreetMap - Dados Viários
- SRE (Secretaria de Obras) - Estradas Estaduais
- Prefeituras - Portais de Dados Abertos

**Fontes Complementares:**
- CNAE - Cartografia
- INCRA - Georreferenciamento
- ANTT - Transportes

---

**Data de Início**: 15 de Janeiro de 2026  
**Status**: 🔄 Em Desenvolvimento  
**Versão**: 1.0 - Versão Completa com Progresso
