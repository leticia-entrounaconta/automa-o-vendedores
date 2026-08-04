import logging
from pathlib import Path

import pandas as pd

from app.browser.downloads import aguardar_novo_download, arquivos_atuais, validar_download_excel
from app.settings.config import DOWNLOAD_DIR, WAIT_DOWNLOAD
from app.validations.files import garantir_dataframe_nao_vazio
from app.data_processing.export_handler import exportar_excel_atomico


VENDEDORES_REMOVER = [
    "camila kawai",
    "enc-colaboradores",
    "enc+",
    "improdutivo",
    "não identificado",
    "sem atuação",
]


def snapshot_downloads(download_dir: Path = DOWNLOAD_DIR) -> set[Path]:
    """Compatibility wrapper for the centralized download snapshot."""
    return arquivos_atuais(download_dir)


def wait_download(
    arquivos_antes: set[Path] | None = None,
    timeout: int = WAIT_DOWNLOAD,
    extensions: tuple[str, ...] = (".xlsx", ".xls", ".csv"),
    download_dir: Path = DOWNLOAD_DIR,
) -> Path:
    """Wait for a new, stable and readable spreadsheet download."""
    previous_files = arquivos_antes if arquivos_antes is not None else snapshot_downloads(download_dir)
    return aguardar_novo_download(download_dir, previous_files, timeout, extensions)


def check_download(file_path: Path) -> bool:
    try:
        validar_download_excel(file_path)
        return True
    except Exception:
        return False


def save_non_empty_excel(dataframe: pd.DataFrame, output_path: Path, contexto: str) -> Path:
    """Wrapper legado para a exportação atômica centralizada."""
    # Mantém a exceção pública anterior para os chamadores e testes existentes.
    garantir_dataframe_nao_vazio(dataframe, contexto)
    return exportar_excel_atomico(dataframe, output_path, contexto)


def clean_excel(file_path: str | Path) -> Path:
    """Compatibility wrapper for the former vendor-cleaning entry point."""
    from app.data_processing.vendedores_handler import tratar_vendedores

    return tratar_vendedores(Path(file_path))
