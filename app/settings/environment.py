"""Centraliza o carregamento do arquivo de ambiente do projeto."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


def load_environment() -> bool:
    """Carrega o ``.env`` da raiz e prioriza seus valores explicitamente."""

    from dotenv import load_dotenv

    return load_dotenv(dotenv_path=ENV_PATH, override=True)
