Atualizei o [README.md](C:/Users/Leticia%20Monteiro/Projetos/automa-vendedores-producao/README.md) e incluí `msal` nas dependências para documentar corretamente o módulo de SharePoint.

# Automação de vendedores e produção 2Tech

Automação Python/Selenium que exporta os vendedores ativos e o Relatório Geral da 2Tech/Gerencial Crédito. Os arquivos são tratados, relacionados e consolidados em uma base para monitoramento comercial.

## O que a automação faz

```text
Login na 2Tech
→ exporta vendedores ativos
→ trata vendedores
→ gera o Relatório Geral de produção
→ trata a produção
→ relaciona por código do vendedor ou CPF/CNPJ
→ calcula indicadores
→ gera planilha consolidada
```

O navegador é encerrado no bloco `finally`, mesmo quando uma etapa falha.

## Arquivos gerados

| Arquivo | Descrição |
| --- | --- |
| `data/downloads/` | Exportações brutas baixadas pela 2Tech. |
| `data/output/vendedores.xlsx` | Vendedores ativos, limpos e deduplicados. |
| `data/output/producao.xlsx` | Produção padronizada e deduplicada por proposta. |
| `data/output/parceiros_classificados.xlsx` | Base final para monitoramento. |
| `logs/app.log` | Log da execução. |
| `data/logs/erros/` | Evidências de falhas Selenium. |

A planilha final possui:

- `DADOS`: uma linha por vendedor;
- `CONTROLE`: período, contagens e versão do processamento;
- `PRODUCOES_NAO_RELACIONADAS`: propostas sem vendedor correspondente, quando houver.

## Regras de dados

### Relacionamento

1. Código do vendedor único;
2. CPF/CNPJ único, somente quando o código não foi localizado;
3. Nome nunca é usado como chave.

Se código e CPF/CNPJ apontarem para parceiros diferentes, a proposta não é relacionada automaticamente e fica na aba de auditoria.

### Data de referência

A data analítica respeita a ordem definida por `PRIORIDADE_DATA_PRODUCAO`:

```text
pagamento → producao → digitacao
```

As três datas são preservadas. A data de digitação não é tratada como pagamento.

### Classificação técnica

| Condição | Classificação |
| --- | --- |
| Cadastro inativo | `CADASTRO_INATIVO` |
| Sem produção relacionada | `SEM_HISTORICO` |
| Menos de 3 meses de histórico | `DADOS_INSUFICIENTES` |
| Menos de 15 dias sem produção | `ATIVO` |
| Entre 15 e 29 dias | `ATENCAO` |
| 30 dias ou mais, com histórico suficiente | `POTENCIAL_REATIVACAO` |

Também são calculados primeira/última produção, propostas, valores em 30/90 dias, médias de 3/6 meses, queda percentual e banco/produto principal por valor.

## Estrutura

```text
app/
├── actions/                 # Login, navegação e exportações Selenium
├── browser/                 # Esperas, cliques, downloads e exceções
├── data_processing/         # Tratamento, indicadores, consolidação e exportação
├── integrations/
│   └── sharepoint.py        # Cliente opcional Microsoft Graph
├── settings/                # Configurações, seletores e driver
├── utils/                   # Evidências de falha
├── validations/             # Validação de arquivos
└── main.py                  # Ponto de entrada
data/
├── downloads/
└── output/
tests/
```

## Instalação

Requer Python 3.11+ e Google Chrome compatível.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Configuração

Crie o arquivo local `.env`:

```powershell
Copy-Item .env.example .env
```

| Variável | Finalidade |
| --- | --- |
| `BASE_URL_2TECH` | URL base do sistema. |
| `USUARIO_2TECH`, `SENHA_2TECH` | Credenciais da 2Tech. |
| `PRODUCAO_ENABLED` | Ativa a coleta de produção. |
| `DATA_INICIAL_PRODUCAO`, `DATA_FINAL_PRODUCAO` | Período manual em `DD/MM/AAAA`. |
| `PRODUCAO_DIAS_HISTORICO` | Período automático quando as datas não forem preenchidas. |
| `DOWNLOAD_PATH`, `OUTPUT_PATH` | Pastas locais de download e saída. |
| `DIAS_ATENCAO`, `DIAS_REATIVACAO` | Limites da classificação técnica. |
| `PRIORIDADE_DATA_PRODUCAO` | Ordem de escolha da data analítica. |
| `STATUS_PRODUCAO_VALIDA` | Status confirmados, separados por vírgula. |

Não versione o `.env` e não registre senhas, tokens ou segredos no Git.

## Relatório Geral

A coleta:

1. Seleciona a aba **Datas**;
2. Preenche o período;
3. Escolhe **Pagamento ao cliente**;
4. Gera o relatório;
5. Aguarda a tabela;
6. Seleciona **Exportar → Excel Resumido**;
7. Confirma um download novo, estável e legível.

## Executar

Feche os arquivos em `data/output` no Excel antes de iniciar.

```powershell
python -m app.main
```

## Testes

Os testes usam dados fictícios e não acessam Selenium, 2Tech nem SharePoint.

```powershell
.\app\.venv\Scripts\python.exe -m pytest -q
```

## SharePoint

O módulo `app/integrations/sharepoint.py` envia arquivos pelo Microsoft Graph, mas o `main.py` ainda não dispara esse envio automaticamente.

Configure no `.env`:

```text
MS_TENANT_ID=
MS_CLIENT_ID=
MS_CLIENT_SECRET=
SHAREPOINT_HOSTNAME=
SHAREPOINT_SITE_PATH=
SHAREPOINT_LIBRARY=
SHAREPOINT_FOLDER=
```

O aplicativo registrado no Microsoft Entra ID precisa ter permissão de escrita na biblioteca de destino.

## Limitações conhecidas

- Cabeçalhos da 2Tech podem mudar; os aliases ficam em `app/data_processing/column_mappings.py`.
- Produção só é confirmada por status quando `STATUS_PRODUCAO_VALIDA` for configurado.
- O envio automático ao SharePoint deve ser habilitado no fluxo principal após confirmar pasta e permissões.