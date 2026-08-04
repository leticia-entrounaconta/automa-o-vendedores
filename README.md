# Automação de vendedores e produção 2Tech

Este projeto exporta os vendedores ativos da 2Tech, coleta o relatório consolidado
de produção, trata os dois arquivos e classifica cada vendedor ativo conforme sua
última produção. A sessão autenticada é reutilizada nas duas coletas.

## Fluxo

1. Inicia o Chrome configurado com pasta de downloads do projeto.
2. Acessa e autentica na 2Tech.
3. Abre **Cadastros > Vendedores**, filtra a situação **Ativo** e exporta os dados.
4. Trata os vendedores, removendo os grupos excluídos já definidos no código.
5. Acessa o relatório consolidado de produção configurado, informa o período e exporta o Excel.
6. Trata datas, valores, duplicidades e identificadores da produção.
7. Valida os dois arquivos, faz um left join e preserva todos os vendedores ativos.
8. Gera a classificação, grava os arquivos locais e encerra o navegador no `finally`.

Os downloads são reconhecidos somente se forem novos em relação ao instante antes
do clique de exportação, não forem temporários e tiverem tamanho estável.

## Base analítica consolidada

A planilha `parceiros_classificados.xlsx` possui uma aba `DADOS`, com uma linha por
vendedor, e uma aba `CONTROLE`, com contagens, período, fonte e versão do
processamento. A consolidação calcula primeira e última produção, propostas e
valores em 30/90 dias, médias mensais de 3/6 meses, queda de 30 dias, banco/produto
principal e a classificação técnica `ATIVO`, `ATENCAO`,
`POTENCIAL_REATIVACAO`, `SEM_HISTORICO`, `CADASTRO_INATIVO` ou
`DADOS_INSUFICIENTES`. Quando houver propostas sem vendedor correspondente, a
planilha também inclui a aba `PRODUCOES_NAO_RELACIONADAS` para auditoria.

Os limites são configuráveis por `DIAS_ATENCAO` e `DIAS_REATIVACAO`. A prioridade
da data analítica é configurável por `PRIORIDADE_DATA_PRODUCAO` e, por padrão, usa
`pagamento,producao,digitacao`. Para evitar transformar uma proposta digitada em
venda confirmada, `STATUS_PRODUCAO_VALIDA` fica vazio até a confirmação dos status
reais exportados pela 2Tech. A limitação e a origem da data permanecem registradas
nos dados.

## Estrutura relevante

```text
app/
├── actions/
│   ├── auth.py                 # Login reutilizado da 2Tech
│   ├── navigation.py           # Navegação existente
│   ├── vendedores.py           # Exportação de vendedores ativos
│   └── producao.py             # Exportação de produção (com seletores confirmáveis)
├── data_processing/
│   ├── vendedores_handler.py   # Tratamento de vendedores
│   ├── producao_handler.py     # Tratamento de produção
│   ├── consolidacao_handler.py # Relação por código/CPF e uma linha por parceiro
│   ├── indicadores_handler.py  # Métricas, médias e qualidade do histórico
│   ├── export_handler.py       # Escrita atômica e abas de auditoria
│   ├── validators.py           # Validações da camada de dados
│   ├── cruzamento_handler.py   # Ponto de compatibilidade e exportação final
│   ├── normalization.py        # Chaves, datas, valores e status padronizados
│   └── column_mappings.py      # Mapeamento centralizado de cabeçalhos 2Tech
├── integrations/sharepoint.py  # Interface futura, sem credenciais
├── browser/
│   ├── waits.py                # Esperas explícitas por operação
│   ├── clicks.py               # Clique com retry e fallback controlado
│   ├── downloads.py            # Download novo, estável e validado
│   └── exceptions.py           # Exceções específicas da automação
├── settings/
│   ├── config.py               # Caminhos e período configurável
│   └── selectors.py            # Todos os locators Selenium
└── validations/files.py        # Proteção contra arquivos vazios
data/
├── downloads/                  # Arquivos brutos temporários
└── output/
    ├── vendedores.xlsx
    ├── producao.xlsx
    └── parceiros_classificados.xlsx
tests/
```

## Instalação

Requer Python 3.11+ e Google Chrome compatível.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

No Linux/macOS, ative o ambiente virtual com o comando equivalente ao shell usado.

## Configuração

Copie o arquivo de exemplo e informe os valores no arquivo local `.env`, que não é
versionado:

```bash
copy .env.example .env
```

Variáveis essenciais:

| Variável | Uso |
| --- | --- |
| `BASE_URL_2TECH` | URL base da plataforma 2Tech. `URL_2TECH` ainda é aceito por compatibilidade. |
| `USUARIO_2TECH` / `SENHA_2TECH` | Credenciais. Os nomes antigos `LOGIN2TECH` e `PASSWORD2TECH` também são aceitos. |
| `DOWNLOAD_PATH` | Pasta de downloads; o padrão é `data/downloads`. |
| `OUTPUT_PATH` | Pasta dos relatórios finais; o padrão é `data/output`. |
| `DATA_INICIAL_PRODUCAO` | Data inicial no formato `DD/MM/AAAA`. |
| `DATA_FINAL_PRODUCAO` | Data final no formato `DD/MM/AAAA`. |
| `RELATORIO_GERAL_URL` | URL do Relatório Geral; por padrão, `relatorioRanking.asp`. |
| `WAIT_PADRAO`, `WAIT_RELATORIO`, `WAIT_DOWNLOAD` | Timeouts específicos, em segundos. |

Se as datas de produção estiverem vazias, o período automático é de 1º de janeiro
do ano atual até a data de execução.

## Produção: Relatório Geral

A coleta acessa diretamente o **Relatório Geral** em `relatorioRanking.asp` e:

1. seleciona a aba **Datas**;
2. preenche o período configurado;
3. escolhe **Pagamento ao cliente** em Tipo de Data;
4. gera o relatório e aguarda `#tableResultado`;
5. abre **Exportar** e escolhe **Excel Resumido**;
6. aceita somente um arquivo novo, estável e legível na pasta de downloads.

O botão azul `+` não é usado no fluxo padrão: na tela ele adiciona um segundo
período obrigatório, e não confirma o filtro já selecionado. A tela
**Operacional > Produção - Layout** continua isolada para importação manual de
arquivos e não participa da coleta.

## Regras do cruzamento e classificação

O cruzamento tenta, nesta ordem, uma chave única de código do vendedor/parceiro e
CPF/CNPJ normalizado. Se as duas chaves apontarem para parceiros diferentes, a
proposta não é relacionada e entra na aba de auditoria. Nomes não são usados como chave: podem ser duplicados,
abreviados ou digitados de maneiras diferentes. Documentos são lidos como texto,
e código, espaços, pontuação, caixa e acentuação são normalizados antes da
comparação. Chaves ambíguas não são associadas por engano.

| Regra técnica | Classificação |
| --- | --- |
| cadastro inativo | `CADASTRO_INATIVO` |
| sem produção relacionada | `SEM_HISTORICO` |
| menos de 3 meses disponíveis | `DADOS_INSUFICIENTES` |
| menos de 15 dias sem produção | `ATIVO` |
| 15 a 29 dias | `ATENCAO` |
| 30 dias ou mais com histórico suficiente | `POTENCIAL_REATIVACAO` |

As médias de 3 e 6 meses incluem meses sem produção como zero somente quando há
histórico suficiente para o período; caso contrário ficam vazias. A queda compara
os últimos 30 dias com os 30 dias anteriores e nunca calcula divisão por zero.

## Executar e testar

```bash
pytest
python -m app.main
```

Os logs são gravados em `logs/app.log`. Em falhas Selenium, screenshot, HTML e
diagnóstico ficam em `data/logs/erros/`, com URL, título, etapa, seletor e exceção.
O resumo final registra status, totais, arquivos e tempo de execução.

## Limitações conhecidas e SharePoint

- Os cabeçalhos exportados pela 2Tech devem ser conferidos na primeira coleta. Os
  aliases ficam centralizados em `app/data_processing/column_mappings.py` para
  ajuste sem espalhar regras pelo projeto.
- A função `enviar_arquivo_sharepoint(caminho_local, nome_remoto)` já isola a
  integração futura. Ela não envia nada até receber uma implementação autenticada
  baseada em variáveis de ambiente ou identidade gerenciada.
