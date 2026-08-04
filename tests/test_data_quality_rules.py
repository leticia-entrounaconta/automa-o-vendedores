from datetime import date

import pandas as pd
import pytest

from app.data_processing.column_mappings import (
    ColumnMappingError,
    PRODUCAO_COLUMN_MAPPING,
    standardize_columns,
)
from app.data_processing.consolidacao_handler import associar_producao_a_vendedores
from app.data_processing.cruzamento_handler import cruzar_vendedores_producao
from app.data_processing.indicadores_handler import calcular_indicadores_por_vendedor
from app.data_processing.normalization import corrigir_texto_corrompido, limpar_texto
from app.data_processing.producao_handler import tratar_dataframe_producao
from app.data_processing.vendedores_handler import tratar_dataframe_vendedores


def _vendedores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "codigo_vendedor": ["001", "002"],
            "cpf_cnpj": ["00123456789", "00987654321"],
            "nome_vendedor": ["Ana", "Bia"],
            "situacao_cadastral": ["Ativo", "Ativo"],
            "grupo_vendedor": ["Comercial", "Comercial"],
        }
    )


def test_ambiguous_alias_is_rejected() -> None:
    raw = pd.DataFrame({"Código Corretor": ["1"], "Código Vendedor": ["1"]})
    with pytest.raises(ColumnMappingError, match="codigo_vendedor"):
        standardize_columns(raw, PRODUCAO_COLUMN_MAPPING)


def test_text_cleanup_and_safe_encoding_correction() -> None:
    assert limpar_texto("  Ana\u00a0  Maria ") == "Ana Maria"
    assert corrigir_texto_corrompido("JOÃƒO") == "JOÃO"
    assert corrigir_texto_corrompido("PRODUÇÃO") == "PRODUÇÃO"


def test_groups_and_duplicate_sellers_are_handled() -> None:
    raw = pd.DataFrame(
        {
            "Código Vendedor": ["001", "001", "002"],
            "Nome Vendedor": ["Ana", "Ana Silva", "Ignorado"],
            "Situação Vendedor": ["Ativo", "Ativo", "Ativo"],
            "Grupo Vendedor": ["Comercial", "Comercial", "ENC+"],
            "Cadastro": ["01/01/2026", "02/01/2026", "01/01/2026"],
        }
    )
    result = tratar_dataframe_vendedores(raw)
    assert len(result) == 1
    assert result.loc[0, "nome_vendedor"] == "Ana Silva"


def test_duplicate_proposal_prefers_latest_update_and_payment_date() -> None:
    raw = pd.DataFrame(
        {
            "Código Corretor": ["001", "001"],
            "Nº Proposta/ADE": ["P-1", "P-1"],
            "Valor Bruto": ["100,00", "200,00"],
            "Data de Digitação": ["01/01/2026", "02/01/2026"],
            "Data de Pagamento": ["03/01/2026", "04/01/2026"],
            "DataStatusEsteira": ["05/01/2026", "06/01/2026"],
        }
    )
    result = tratar_dataframe_producao(raw)
    assert len(result) == 1
    assert result.loc[0, "valor_producao"] == 200.0
    assert result.loc[0, "origem_data_referencia"] == "pagamento"
    assert bool(result.loc[0, "possui_data_pagamento"])


def test_conflicting_code_and_document_is_not_related() -> None:
    production = pd.DataFrame(
        {"codigo_vendedor": ["001"], "cpf_cnpj": ["00987654321"], "numero_proposta": ["P1"]}
    )
    result = associar_producao_a_vendedores(_vendedores(), production)
    assert result.loc[0, "chave_relacionamento"] == "nao_relacionado"
    assert result.loc[0, "motivo_nao_relacionamento"] == "conflito_codigo_documento"


def test_six_month_history_and_principal_fields() -> None:
    dates = pd.date_range("2026-02-15", periods=6, freq="MS")
    production = pd.DataFrame(
        {
            "_vendedor_id": [0] * 6,
            "numero_proposta": [f"P{i}" for i in range(6)],
            "data_referencia_producao": dates,
            "valor_producao": [10, 10, 10, 10, 10, 100],
            "banco": ["A", "A", "A", "B", "B", "B"],
            "produto": ["X", "X", "X", "Y", "Y", "Y"],
        }
    )
    indicator = calcular_indicadores_por_vendedor(production, pd.Timestamp("2026-08-03")).iloc[0]
    assert indicator["historico_suficiente_6_meses"]
    assert indicator["media_mensal_6_meses"] is not pd.NA
    assert indicator["banco_principal_por_valor"] == "B"
    assert indicator["produto_principal_por_valor"] == "Y"


def test_insufficient_history_and_zero_denominator_do_not_create_fake_drop() -> None:
    production = pd.DataFrame(
        {
            "_vendedor_id": [0], "numero_proposta": ["P1"],
            "data_referencia_producao": ["2026-08-01"], "valor_producao": [100.0],
        }
    )
    indicator = calcular_indicadores_por_vendedor(production, pd.Timestamp("2026-08-03")).iloc[0]
    assert indicator["primeira_producao"] == pd.Timestamp("2026-08-01")
    assert pd.isna(indicator["media_mensal_6_meses"])
    assert pd.isna(indicator["percentual_queda"])


def test_non_related_production_creates_audit_sheet(tmp_path) -> None:
    sellers_path, production_path, output_path = (
        tmp_path / "vendedores.xlsx", tmp_path / "producao.xlsx", tmp_path / "final.xlsx"
    )
    _vendedores().to_excel(sellers_path, index=False)
    pd.DataFrame(
        {
            "codigo_vendedor": ["999"], "cpf_cnpj": [""], "numero_proposta": ["P9"],
            "data_referencia_producao": ["2026-08-01"], "valor_producao": [10],
        }
    ).to_excel(production_path, index=False)
    cruzar_vendedores_producao(sellers_path, production_path, output_path, date(2026, 8, 3))
    workbook = pd.ExcelFile(output_path)
    assert "PRODUCOES_NAO_RELACIONADAS" in workbook.sheet_names
    audit = pd.read_excel(output_path, sheet_name="PRODUCOES_NAO_RELACIONADAS")
    assert audit.loc[0, "motivo_nao_relacionamento"] == "vendedor_nao_encontrado"
