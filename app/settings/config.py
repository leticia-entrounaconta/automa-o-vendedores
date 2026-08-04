import logging
import os
from pathlib import Path
from datetime import date, timedelta

from app.settings.environment import load_environment

load_environment()


def ensure_file(path_file: Path) -> str:
    """Ensure file exists and return its string path. If not found, log warning."""
    if not path_file.is_file():
        logging.warning(f"Arquivo nao encontrado: {path_file}")
    return str(path_file)


# ── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = BASE_DIR / "data"
ERROR_EVIDENCE_DIR = DATA_DIR / "logs" / "erros"


def _configured_path(variable_name: str, default: Path) -> Path:
    """Resolve an optional environment path relative to the project root."""
    configured = os.getenv(variable_name)
    if not configured:
        return default

    path = Path(configured).expanduser()
    return path if path.is_absolute() else BASE_DIR / path


DOWNLOAD_DIR = _configured_path("DOWNLOAD_PATH", DATA_DIR / "downloads")
OUTPUT_DIR = _configured_path("OUTPUT_PATH", DATA_DIR / "output")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ERROR_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

VENDEDORES_OUTPUT_PATH = OUTPUT_DIR / "vendedores.xlsx"
PRODUCAO_OUTPUT_PATH = OUTPUT_DIR / "producao.xlsx"
PARCEIROS_CLASSIFICADOS_OUTPUT_PATH = OUTPUT_DIR / "parceiros_classificados.xlsx"

# ── URLs — configure in .env ─────────────────────────────────────────────────

BASE_URL = os.getenv("BASE_URL_2TECH") or os.getenv("URL")
BASE_URL_2TECH = os.getenv("BASE_URL_2TECH") or os.getenv("URL_2TECH")
# O Relatório Geral é a fonte de produção. A variável antiga continua aceita
# para não quebrar arquivos .env já existentes.
RELATORIO_GERAL_URL = (
    os.getenv("RELATORIO_GERAL_URL")
    or os.getenv("RELATORIO_PRODUCAO_URL")
    or "https://app1.gerencialcredito.com.br/Entrounaconta/relatorioRanking.asp"
)
RELATORIO_PRODUCAO_URL = RELATORIO_GERAL_URL


def get_periodo_producao() -> tuple[str, str]:
    """Calcula automaticamente o período do relatório de produção.

    A data final será o dia atual.
    A data inicial será calculada com base na quantidade de dias definida em
    PRODUCAO_DIAS_HISTORICO.

    Caso DATA_INICIAL_PRODUCAO ou DATA_FINAL_PRODUCAO estejam preenchidas no
    .env, elas serão usadas como substituição manual.
    """

    hoje = date.today()

    dias_historico_texto = os.getenv(
        "PRODUCAO_DIAS_HISTORICO",
        "120",
    )

    try:
        dias_historico = int(dias_historico_texto)
    except ValueError as error:
        raise ValueError(
            "PRODUCAO_DIAS_HISTORICO deve ser um número inteiro."
        ) from error

    if dias_historico <= 0:
        raise ValueError(
            "PRODUCAO_DIAS_HISTORICO deve ser maior que zero."
        )

    data_inicial_automatica = hoje - timedelta(
        days=dias_historico
    )

    data_inicial = os.getenv(
        "DATA_INICIAL_PRODUCAO"
    ) or data_inicial_automatica.strftime(
        "%d/%m/%Y"
    )

    data_final = os.getenv(
        "DATA_FINAL_PRODUCAO"
    ) or hoje.strftime(
        "%d/%m/%Y"
    )

    return data_inicial, data_final

# ── Timeouts ─────────────────────────────────────────────────────────────────

WAIT_PADRAO = int(os.getenv("WAIT_PADRAO", "20"))
WAIT_RELATORIO = int(os.getenv("WAIT_RELATORIO", "60"))
WAIT_DOWNLOAD = int(os.getenv("WAIT_DOWNLOAD", "120"))
MAX_TENTATIVAS = int(os.getenv("MAX_TENTATIVAS", "3"))

# Regras analíticas. Status ficam vazios até serem confirmados no relatório
# exportado; assim uma proposta digitada não é tratada como venda por engano.
STATUS_PRODUCAO_VALIDA = tuple(
    status.strip()
    for status in os.getenv("STATUS_PRODUCAO_VALIDA", "").split(",")
    if status.strip()
)
PRIORIDADE_DATA_PRODUCAO = tuple(
    item.strip().lower()
    for item in os.getenv(
        "PRIORIDADE_DATA_PRODUCAO", "pagamento,producao,digitacao"
    ).split(",")
    if item.strip().lower() in {"pagamento", "producao", "digitacao"}
)
if not PRIORIDADE_DATA_PRODUCAO:
    raise ValueError(
        "PRIORIDADE_DATA_PRODUCAO deve conter pagamento, producao e/ou digitacao."
    )
DIAS_ATENCAO = int(os.getenv("DIAS_ATENCAO", "15"))
DIAS_REATIVACAO = int(os.getenv("DIAS_REATIVACAO", "30"))

PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "60"))
ELEMENT_WAIT_TIMEOUT = 0
EXPLICITLY_WAIT = WAIT_PADRAO

# ── Derived paths ────────────────────────────────────────────────────────────

LOG_FILE_PATH = str(LOGS_DIR / "app.log")
DOWNLOAD_PATH = str(DOWNLOAD_DIR)
