# RPA Template

Template para criação de projetos de Robotic Process Automation (RPA) com Selenium e Docker, configurado com:

- **Selenium + Chrome** - automação web com download configurado
- **Variáveis de ambiente** - credenciais, URLs, MS Graph e opções do container via `.env`
- **Logging rotativo** - saída em console e arquivo `logs/app.log`
- **Docker** - container com Chrome e VNC opcional para debugging visual
- **Utilitários de RPA** - navegação, autenticação, datas úteis, downloads e Excel

## Estrutura

```
├── app/
│   ├── main.py                  # Entry point - customize com sua lógica RPA
│   ├── actions/                 # Interações Selenium (click, fill, navigate)
│   ├── data_processing/         # Tratamento de dados, datas, exceções
│   ├── settings/
│   │   ├── config.py            # Paths, URLs, timeouts
│   │   ├── driver_settings.py   # WebDriver Chrome singleton
│   │   ├── logging_config.py    # Rotating file + console logger
│   │   ├── environment.py       # Carregamento do .env
│   │   └── secrets.py           # Credenciais via variáveis de ambiente
│   ├── ui/                      # Login, cookies
│   └── utils/                   # Cores ANSI, helpers
├── docker/entrypoint.sh         # Entrypoint com VNC opcional
├── Dockerfile
├── docker-compose.yml
└── .env.example                 # Variáveis de ambiente
```

## Como usar este template

### 1. Criar novo repositório a partir do template

```bash
# No GitHub: "Use this template" → Create a new repository
# Ou via CLI:
gh repo create Entrounaconta/meu-novo-rpa --template Entrounaconta/rpa-template --private
git clone git@github.com:Entrounaconta/meu-novo-rpa.git
cd meu-novo-rpa
```

### 2. Configurar ambiente local

```bash
cp .env.example .env
# Edite .env com suas credenciais e URLs

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configurar variáveis de ambiente

O arquivo `.env.example` lista as variáveis esperadas pelo template:

| Variável | Uso |
|---|---|
| `URL`, `URL_2TECH` | URLs base usadas nos helpers de navegação |
| `LOGIN`, `PASSWORD`, `LOGIN2TECH`, `PASSWORD2TECH` | Credenciais carregadas por `app/settings/secrets.py` |
| `APP_ID`, `SECRET_KEY`, `TENANT_ID`, `GROUP_ID` | Configurações opcionais para integrações com MS Graph |
| `WEBHOOK_URL` | Webhook opcional carregado por `app/settings/secrets.py` |
| `ENABLE_VNC` | Define se o container inicia a pilha visual com noVNC |
| `APP_MODULE` | Módulo Python executado pelo entrypoint Docker |
| `LOG_LEVEL`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT` | Configuração do logging rotativo |

### 4. Implementar sua automação

Edite `app/main.py` e implemente os passos do seu RPA:

```python
def main():
    start_time = time()
    logger.info("Inicio da execucao do RPA...")

    try:
        login_no_portal()
        navegar_ate_relatorio()
        processar_dados()
    except Exception as error:
        logger.exception("Erro durante execucao: %s", error)
        raise
    finally:
        driver.quit()
```

### 5. Executar

```bash
# Local
python -m app.main

# Docker
docker compose up --build

# Docker com VNC (debug visual)
ENABLE_VNC=true docker compose up --build
# Acesse http://localhost:7900 para ver o navegador
```

## Configuração

### Secrets

Os secrets são lidos de variáveis de ambiente carregadas por `python-dotenv`:

```python
from app.settings.secrets import login, password, webhook_url
```

Para adicionar uma nova credencial, inclua a variável no `.env` e leia com `os.getenv()` ou com o helper `check_env_variable()`.

### Logging

`app/settings/logging_config.py` configura o logger raiz com console e `RotatingFileHandler`. Por padrão, os logs são gravados em `logs/app.log`.

As variáveis abaixo ajustam o comportamento:

- `LOG_LEVEL`: nível de log, com default `INFO`
- `LOG_MAX_BYTES`: tamanho máximo de cada arquivo de log, com default `5242880`
- `LOG_BACKUP_COUNT`: quantidade de backups mantidos, com default `5`

### WebDriver

`app/settings/driver_settings.py` cria um Chrome WebDriver configurado com diretório de download em `app/temp_files`. Quando `ENABLE_VNC` é `false`, o Chrome roda em modo headless.

## Tecnologias

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ local; Python 3.13 no Dockerfile |
| Automação | Selenium + Chrome |
| Configuração | python-dotenv + variáveis de ambiente |
| Dados | pandas + openpyxl |
| Datas úteis | holidays + python-dateutil |
| Logging | logging + RotatingFileHandler |
| Container | Docker + Chrome + VNC |
| Qualidade | pyproject com parâmetros para ruff, mypy e bandit |
