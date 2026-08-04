from pathlib import Path

import pandas as pd
import pytest

from app.browser.downloads import arquivos_atuais, validar_download_excel
from app.browser.exceptions import ReportValidationError


def test_validar_download_excel_accepts_readable_spreadsheet(tmp_path: Path) -> None:
    report = tmp_path / "producao.xlsx"
    pd.DataFrame({"CPF": ["00123456789"], "Data": ["01/01/2026"]}).to_excel(report, index=False)

    validar_download_excel(report, required_columns=("CPF",))


def test_validar_download_excel_reports_missing_column(tmp_path: Path) -> None:
    report = tmp_path / "producao.xlsx"
    pd.DataFrame({"Nome": ["Ana"]}).to_excel(report, index=False)

    with pytest.raises(ReportValidationError, match="CPF"):
        validar_download_excel(report, required_columns=("CPF",))


def test_arquivos_atuais_uses_only_target_directory(tmp_path: Path) -> None:
    (tmp_path / "novo.xlsx").write_bytes(b"conteudo")
    assert (tmp_path / "novo.xlsx").resolve() in arquivos_atuais(tmp_path)
