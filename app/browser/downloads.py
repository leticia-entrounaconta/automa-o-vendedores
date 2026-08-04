"""Download detection and validation isolated from Selenium actions."""

from __future__ import annotations

import logging
from pathlib import Path
from time import monotonic, sleep
from typing import Iterable

import pandas as pd

from app.browser.exceptions import DownloadError, ReportValidationError
from app.settings.config import DOWNLOAD_DIR, WAIT_DOWNLOAD

logger = logging.getLogger(__name__)
TEMPORARY_EXTENSIONS = {".crdownload", ".tmp", ".part"}


def arquivos_atuais(pasta: Path = DOWNLOAD_DIR) -> set[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    return {path.resolve() for path in pasta.iterdir()}


def _arquivo_estavel(path: Path, checks: int = 2, interval: float = 0.5) -> bool:
    previous_size: int | None = None
    stable_checks = 0
    for _ in range(checks + 1):
        if not path.is_file() or path.stat().st_size == 0:
            return False
        size = path.stat().st_size
        stable_checks = stable_checks + 1 if size == previous_size else 0
        if stable_checks >= checks:
            return True
        previous_size = size
        sleep(interval)
    return False


def validar_download_excel(path: Path, required_columns: Iterable[str] = ()) -> None:
    if path.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
        raise DownloadError(f"Extensão não suportada para relatório: {path.suffix}")
    if not path.is_file() or path.stat().st_size == 0:
        raise DownloadError(f"Arquivo baixado inexistente ou vazio: {path}")
    try:
        dataframe = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
    except Exception as error:
        raise ReportValidationError(f"Arquivo baixado não abre como planilha: {path}") from error
    if dataframe.empty:
        raise ReportValidationError(f"Relatório baixado está vazio: {path}")
    columns = {str(column).strip() for column in dataframe.columns}
    missing = [column for column in required_columns if column not in columns]
    if missing:
        raise ReportValidationError(
            f"Relatório baixado não contém as colunas obrigatórias {missing}. "
            f"Colunas encontradas: {sorted(columns)}"
        )


def aguardar_novo_download(
    pasta: Path,
    arquivos_anteriores: set[Path],
    timeout: int = WAIT_DOWNLOAD,
    extensoes: Iterable[str] = (".xlsx", ".xls", ".csv"),
    required_columns: Iterable[str] = (),
) -> Path:
    """Return only a new, stable and readable file created after the export click."""
    accepted_extensions = {extension.lower() for extension in extensoes}
    started_at = monotonic()
    while monotonic() - started_at < timeout:
        candidates = [
            path
            for path in arquivos_atuais(pasta) - arquivos_anteriores
            if path.suffix.lower() in accepted_extensions and path.suffix.lower() not in TEMPORARY_EXTENSIONS
        ]
        if candidates:
            candidate = max(candidates, key=lambda path: path.stat().st_mtime)
            if _arquivo_estavel(candidate):
                validar_download_excel(candidate, required_columns)
                logger.info("download | concluído | arquivo=%s", candidate)
                return candidate
        sleep(0.5)
    raise DownloadError(f"Nenhum novo download válido foi concluído em {timeout}s na pasta {pasta}")
