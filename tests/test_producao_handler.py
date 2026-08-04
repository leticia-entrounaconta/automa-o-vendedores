import pandas as pd
import pytest

from app.data_processing.excel_handler import save_non_empty_excel
from app.data_processing.producao_handler import tratar_dataframe_producao
from app.validations.files import ArquivoVazioError


def test_invalid_production_dates_are_removed_safely() -> None:
    raw = pd.DataFrame(
        {
            "Código Vendedor": ["001", "001"],
            "Data Produção": ["31/07/2026", "data inválida"],
            "Nº Proposta": ["P1", "P2"],
            "Valor Produção": ["R$ 1.250,50", "R$ 100,00"],
        }
    )
    treated = tratar_dataframe_producao(raw)
    assert len(treated) == 1
    assert treated.iloc[0]["valor_producao"] == 1250.5


def test_empty_dataframe_does_not_replace_existing_file(tmp_path) -> None:
    output_path = tmp_path / "valid.xlsx"
    save_non_empty_excel(pd.DataFrame({"valor": [1]}), output_path, "arquivo válido")
    original_size = output_path.stat().st_size

    with pytest.raises(ArquivoVazioError):
        save_non_empty_excel(pd.DataFrame(), output_path, "arquivo vazio")

    assert output_path.is_file()
    assert output_path.stat().st_size == original_size


def test_excel_resumido_uses_data_digitacao_as_available_date_reference() -> None:
    raw = pd.DataFrame(
        {
            "Código Corretor": ["000123"],
            "Corretor": ["Parceiro Teste"],
            "Nº Proposta/ADE": ["PROP-1"],
            "Data de Digitação": ["03/08/2026"],
            "Valor Bruto": ["R$ 1.250,50"],
        }
    )

    treated = tratar_dataframe_producao(raw)

    assert treated.loc[0, "codigo_vendedor"] == "000123"
    assert treated.loc[0, "numero_proposta"] == "PROP1"
    assert pd.isna(treated.loc[0, "data_producao"])
    assert treated.loc[0, "data_referencia_producao"] == pd.Timestamp("2026-08-03")
    assert treated.loc[0, "origem_data_referencia"] == "digitacao"
    assert treated.loc[0, "valor_producao"] == 1250.5
