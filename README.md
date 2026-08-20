Automação de vendedores e produção

Automação em Python e Selenium para coletar vendedores ativos e o Relatório Geral da 2Tech/Gerencial Crédito. As bases são tratadas, relacionadas por identificadores confiáveis e consolidadas para acompanhamento comercial.

## Fluxo da automação

```text
Login na 2Tech
→ exportação de vendedores ativos
→ tratamento dos vendedores
→ Relatório Geral (Pagamento ao cliente)
→ tratamento da produção
→ cruzamento das bases
→ parceiros_classificados.xlsx
→ envio opcional ao SharePoint
```

O WebDriver é encerrado no bloco `finally`, inclusive quando ocorre uma falha.

## Arquivos gerados

| Caminho | Conteúdo |
| --- | --- |
| `data/downloads/` | Arquivos brutos baixados durante a execução. |
| `data/output/vendedores.xlsx` | Vendedores ativos, limpos e deduplicados. |
| `data/output/producao.xlsx` | Produção padronizada e deduplicada por proposta. |
| `data/output/parceiros_classificados.xlsx` | Base consolidada para monitoramento. |
| `logs/app.log` | Log rotativo da aplicação. |
| `data/logs/erros/` | Screenshot, HTML e detalhes de falhas Selenium. |

O arquivo final contém as abas `DADOS`, `CONTROLE` e, quando necessário, `PRODUCOES_NAO_RELACIONADAS`.

## Regras de negócio

### Cruzamento de vendedores e produção

A produção é relacionada nesta ordem:

1. Código do vendedor;
2. CPF/CNPJ normalizado, somente quando o código não localizar o vendedor;
3. Nome não é usado como chave de relacionamento.

Se código e CPF/CNPJ identificarem vendedores diferentes, a proposta é mantida para auditoria e não é relacionada automaticamente.

### Data de referência

A data analítica de cada proposta segue a ordem configurada em `PRIORIDADE_DATA_PRODUCAO`:

```text
pagamento → producao → digitacao
```

As datas originais são preservadas. A data de digitação não é considerada pagamento.

### Classificação

| Condição | Classificação |
| --- | --- |
| Cadastro inativo | `CADASTRO_INATIVO` |
| Sem produção relacionada | `SEM_HISTORICO` |
| Menos de três meses de histórico | `DADOS_INSUFICIENTES` |
| Menos de 15 dias sem produção | `ATIVO` |
| Entre 15 e 29 dias sem produção | `ATENCAO` |
| 30 dias ou mais, com histórico suficiente | `POTENCIAL_REATIVACAO` |

Além da classificação, a planilha final inclui primeira e última produção, propostas, valores de 30/90 dias, médias e banco/produto predominante.

## Estrutura

```text
app/
├── actions/                 # Login, navegação e coleta Selenium
├── browser/                 # Driver, cliques, esperas, downloads e exceções
├── data_processing/         # Tratamento, indicadores, consolidação e exportação
├── integrations/
│   └── sharepoint.py        # Integração opcional com Microsoft Graph
├── settings/                # Ambiente, configurações, seletores e logs
├── utils/                   # Evidências de falha
├── validations/             # Validação de planilhas
└── main.py                  # Ponto de entrada
data/
├── downloads/
└── output/
scripts/
└── test_sharepoint_auth.py  # Teste isolado de autenticação Graph
tests/
```

## Pré-requisitos e instalação

- Python 3.11 ou superior;
- Google Chrome compatível com o Selenium;
- acesso à 2Tech/Gerencial Crédito.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

## Configuração

O `.env` é local, não deve ser versionado e é carregado sempre a partir da raiz do projeto. Seus valores têm prioridade sobre variáveis antigas da sessão do PowerShell ou do Windows.

| Variável | Descrição |
| --- | --- |
| `USUARIO_2TECH`, `SENHA_2TECH` | Credenciais do sistema. |
| `BASE_URL_2TECH` | URL base da 2Tech. |
| `RELATORIO_GERAL_URL` | URL do Relatório Geral. |
| `PRODUCAO_ENABLED` | Define se a coleta de produção será executada. |
| `DATA_INICIAL_PRODUCAO`, `DATA_FINAL_PRODUCAO` | Período manual, no formato `DD/MM/AAAA`. |
| `PRODUCAO_DIAS_HISTORICO` | Período automático quando datas manuais não forem informadas. |
| `DOWNLOAD_PATH`, `OUTPUT_PATH` | Pastas de download e saída, relativas à raiz ou absolutas. |
| `WAIT_PADRAO`, `WAIT_RELATORIO`, `WAIT_DOWNLOAD` | Limites de espera em segundos. |
| `MAX_TENTATIVAS` | Número máximo de tentativas em etapas instáveis. |
| `PRIORIDADE_DATA_PRODUCAO` | Ordem para selecionar a data analítica da proposta. |
| `STATUS_PRODUCAO_VALIDA` | Status válidos de produção, separados por vírgula. |

### Relatório Geral

Com `PRODUCAO_ENABLED=true`, a automação acessa o Relatório Geral e:

1. garante a aba **Datas**;
2. preenche o período;
3. seleciona **Pagamento ao cliente** pelo componente visual da página;
4. gera o relatório;
5. aguarda os resultados;
6. seleciona **Exportar → Excel Resumido**;
7. confirma o novo download antes do tratamento.

## Execução

Antes de executar, feche no Excel os arquivos presentes em `data/output/`.

```powershell
python -m app.main
```

Quando `PRODUCAO_ENABLED=false`, somente o relatório de vendedores é processado e a execução termina com sucesso parcial.

## Execução com Docker

O Docker empacota o Python, o Google Chrome e o ambiente gráfico virtual usados
pelo Selenium. Assim, a automação executa da mesma forma em qualquer máquina
que tenha Docker, sem instalar Python, Chrome ou ChromeDriver localmente.

1. Crie o arquivo de configuração e preencha as credenciais:

```powershell
Copy-Item .env.example .env
```

2. Construa a imagem e execute a automação:

```powershell
docker compose up --build
```

Os arquivos gerados continuam disponíveis na máquina anfitriã em `data/` e os
logs em `logs/`, pois essas pastas são montadas no contêiner. A imagem não copia
o `.env`; o Compose o injeta apenas durante a execução, evitando incluir
credenciais na imagem. Arquivos de dados e testes também são excluídos da etapa
de construção, reduzindo o tamanho enviado ao Docker sem afetar a execução.

Por padrão, `ENABLE_VNC=false` executa o Chrome sem interface, que é o modo mais
leve para rotina. Para acompanhar visualmente a automação, defina
`ENABLE_VNC=true` e `HEADLESS=false` no `.env`, execute novamente e abra
`http://localhost:7900` no navegador. O acesso VNC é destinado apenas ao uso
local: não exponha essa porta em servidores públicos.

Para encerrar e remover o contêiner após uma execução, use:

```powershell
docker compose down
```

## Agendamento semanal no Windows

O projeto inclui `run_rpa.ps1`, que executa `docker compose run --rm rpa` e
repassa o código de saída do contêiner ao Windows. Para instalar uma tarefa
semanal, use `install_scheduled_task.ps1` em um PowerShell aberto como
**Administrador**:

```powershell
.\install_scheduled_task.ps1
```

Informe a senha da conta Windows que já possui acesso ao Docker Desktop. O PIN
do Windows Hello não serve para essa finalidade e a senha não é salva no
projeto nem exibida nos logs.

A tarefa é configurada para rodar toda segunda-feira às 15:00, com privilégios
elevados, inicialização após um horário perdido, despertar do computador e
bloqueio de execuções simultâneas. Em caso de falha na instalação, consulte
`logs/scheduled_task_setup.log`.

Antes de agendar a execução de produção, confirme no `.env`:

```env
ENABLE_VNC=false
HEADLESS=true
PRODUCAO_ENABLED=true
SHAREPOINT_ENABLED=true
```

O Docker Desktop deve estar disponível para a mesma conta que executará a
tarefa. Como o Docker Desktop normalmente é iniciado quando o usuário entra no
Windows, valide o cenário após reinicialização antes de depender de execução
sem usuário conectado. Para acompanhar uma execução, abra o Agendador de
Tarefas, execute a tarefa manualmente e confira **Último resultado da
execução**: `0x0` indica sucesso; qualquer outro valor indica falha. Os detalhes
da automação permanecem em `logs/app.log` e as evidências de Selenium em
`data/logs/erros/`.

## Testes

Os testes unitários usam dados fictícios e não acessam Selenium, 2Tech ou SharePoint.

```powershell
python -m pytest -q
```

## SharePoint

O envio é opcional e só ocorre ao final de uma execução completa, depois de os três arquivos locais serem gerados.

```env
SHAREPOINT_ENABLED=false
MS_TENANT_ID=
MS_CLIENT_ID=
MS_CLIENT_SECRET=
SHAREPOINT_HOSTNAME=entrounaconta.sharepoint.com
SHAREPOINT_SITE_PATH=/sites/Tienc
SHAREPOINT_LIBRARY=
SHAREPOINT_FOLDER=
```

Para habilitar, altere `SHAREPOINT_ENABLED=true`. `MS_CLIENT_SECRET` deve conter exclusivamente o campo **Value** de um segredo ativo criado para o mesmo aplicativo informado em `MS_CLIENT_ID`; nunca use Secret ID, Object ID ou Application ID.

Quando estiver desabilitado, o sistema não solicita token, não chama o Microsoft Graph e registra `Integração com SharePoint desabilitada.`

### Teste isolado de autenticação

O comando abaixo verifica apenas o carregamento do `.env` e a obtenção do token. Ele não abre o navegador e não realiza upload.

```powershell
python scripts/test_sharepoint_auth.py
```

O teste mostra somente o Tenant, Client ID, se o segredo foi preenchido e seu tamanho. Nem o segredo nem o token são registrados.

Se a autenticação funcionar, mas a consulta ao site retornar `401` ou `403`, confira as permissões de aplicação no Microsoft Entra e a autorização do aplicativo para o site e a biblioteca configurados.

## Solução de problemas

| Situação | Ação recomendada |
| --- | --- |
| `AADSTS7000215` | Crie ou copie novamente o **Value** de um segredo ativo no mesmo registro do `MS_CLIENT_ID`. |
| Arquivo de saída bloqueado | Feche o arquivo no Excel e execute novamente. |
| Falha Selenium | Consulte `data/logs/erros/` para screenshot, HTML e detalhes da etapa. |
| Download não localizado | Confira `DOWNLOAD_PATH`, permissões da pasta e arquivos temporários `.crdownload`. |
| Cabeçalho da exportação mudou | Atualize os aliases em `app/data_processing/column_mappings.py`. |

## Segurança

- Nunca versione `.env`, `.env.local` ou `.env.production`.
- Não registre senhas, tokens ou Client Secret em logs, código ou documentação.
- Se um segredo for exposto, revogue-o no Microsoft Entra e crie outro imediatamente.

## Limitações conhecidas

- A validação de produção por status depende da confirmação e configuração de `STATUS_PRODUCAO_VALIDA`.
- Alterações de HTML, textos ou cabeçalhos na plataforma podem exigir ajuste de seletores e mapeamentos.
- O upload ao SharePoint depende de credenciais válidas e das permissões de aplicação no site configurado.
