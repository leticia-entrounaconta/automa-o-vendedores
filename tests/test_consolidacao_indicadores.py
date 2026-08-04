from datetime import date

import pandas as pd
import pytest

from app.data_processing.column_mappings import PRODUCAO_COLUMN_MAPPING, standardize_columns
from app.data_processing.consolidacao_handler import associar_producao_a_vendedores, consolidar_vendedores_producao
from app.data_processing.cruzamento_handler import cruzar_vendedores_producao
from app.data_processing.export_handler import (
    ArquivoSaidaBloqueadoError,
    _substituir_arquivo_temporario,
    exportar_excel_atomico,
)
from app.data_processing.indicadores_handler import calcular_indicadores_por_vendedor
from app.data_processing.normalization import normalizar_data, normalizar_valor_monetario
from app.data_processing.validators import DataProcessingValidationError, validar_colunas_obrigatorias


def _vendedores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "codigo_vendedor": ["001", "002"],
            "cpf_cnpj": ["00123456789", "00987654321"],
            "nome_vendedor": ["Ana", "Bia"],
            "situacao_cadastral": ["ATIVO", "ATIVO"],
            "grupo_vendedor": ["A", "B"],
        }
    )


def _producao() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "codigo_vendedor": ["001", "001", "999"],
            "cpf_cnpj": ["", "", ""],
            "numero_proposta": ["P1", "P2", "P3"],
            "data_referencia_producao": pd.to_datetime(["2026-07-31", "2026-06-20", "2026-07-20"]),
            "origem_data_referencia": ["producao", "digitacao", "producao"],
            "valor_producao": [100.0, 200.0, 1.0],
            "banco": ["Banco A", "Banco B", "Banco C"],
            "produto": ["Produto A", "Produto B", "Produto C"],
        }
    )


def test_aliases_dates_and_currency_are_normalized() -> None:
    frame = standardize_columns(pd.DataFrame({"Código Corretor": ["001"]}), PRODUCAO_COLUMN_MAPPING)
    assert "codigo_vendedor" in frame
    assert normalizar_data(pd.Series(["03/08/2026", "inválida"])).notna().sum() == 1
    assert normalizar_valor_monetario(pd.Series(["R$ 1.234,50"])).iloc[0] == 1234.5


def test_missing_required_columns_raise_clear_error() -> None:
    with pytest.raises(DataProcessingValidationError, match="numero_proposta"):
        validar_colunas_obrigatorias(pd.DataFrame({"codigo_vendedor": ["1"]}), {"codigo_vendedor", "numero_proposta"}, "produção")


def test_association_uses_code_then_document_never_name() -> None:
    vendors = _vendedores()
    production = _producao().iloc[[0, 2]].copy()
    segundo_indice = production.index[1]
    production.loc[segundo_indice, "codigo_vendedor"] = ""
    production.loc[segundo_indice, "cpf_cnpj"] = "00987654321"
    production.loc[segundo_indice, "nome_vendedor"] = "Ana"  # nome deliberadamente incorreto
    associated = associar_producao_a_vendedores(vendors, production)
    assert associated["_vendedor_id"].notna().all()
    assert associated.loc[segundo_indice, "chave_relacionamento"] == "cpf_cnpj"


def test_production_without_registered_seller_is_identified() -> None:
    associated = associar_producao_a_vendedores(_vendedores(), _producao().iloc[[2]])
    assert associated["_vendedor_id"].isna().all()


def test_indicators_calculate_last_date_days_average_and_drop() -> None:
    associated = _producao().iloc[:2].copy()
    associated["_vendedor_id"] = 0
    result = calcular_indicadores_por_vendedor(associated, pd.Timestamp("2026-08-03")).iloc[0]
    assert result["ultima_producao"] == pd.Timestamp("2026-07-31")
    assert result["dias_sem_producao"] == 3
    assert result["media_mensal_3_meses"] == 100.0  # maio zero, junho 200, julho 100
    assert result["percentual_queda"] == 50.0


def test_consolidation_preserves_one_row_and_classifies_history() -> None:
    final, metrics = consolidar_vendedores_producao(_vendedores(), _producao().iloc[:2], pd.Timestamp("2026-08-20"))
    assert len(final) == 2
    assert metrics["quantidade_parceiros_sem_producao"] == 1
    assert final.loc[final["codigo_vendedor"] == "001", "classificacao_monitoramento"].iloc[0] == "ATENCAO"
    assert final.loc[final["codigo_vendedor"] == "002", "classificacao_monitoramento"].iloc[0] == "SEM_HISTORICO"


def test_final_workbook_has_control_sheet(tmp_path) -> None:
    vendedores = tmp_path / "vendedores.xlsx"
    producao = tmp_path / "producao.xlsx"
    destino = tmp_path / "consolidado.xlsx"
    _vendedores().to_excel(vendedores, index=False)
    _producao().iloc[:2].to_excel(producao, index=False)
    cruzar_vendedores_producao(vendedores, producao, destino, data_referencia=date(2026, 8, 3))
    assert set(pd.ExcelFile(destino).sheet_names) == {"DADOS", "CONTROLE"}
    assert "quantidade_vendedores_processados" in pd.read_excel(destino, sheet_name="CONTROLE").columns


def test_invalid_temporary_export_does_not_replace_valid_file(tmp_path) -> None:
    destino = tmp_path / "saida.xlsx"
    exportar_excel_atomico(pd.DataFrame({"valor": [1]}), destino, "válido")
    tamanho = destino.stat().st_size
    with pytest.raises(DataProcessingValidationError):
        exportar_excel_atomico(pd.DataFrame(), destino, "vazio")
    assert destino.stat().st_size == tamanho


def test_output_file_lock_has_a_clear_error(tmp_path, monkeypatch) -> None:
    temporario = tmp_path / "temporario.xlsx"
    destino = tmp_path / "resultado.xlsx"
    temporario.write_bytes(b"arquivo")

    def bloqueado(_origem, _destino):
        raise PermissionError("arquivo em uso")

    monkeypatch.setattr(type(temporario), "replace", bloqueado)
    with pytest.raises(ArquivoSaidaBloqueadoError, match="Feche o arquivo no Excel"):
        _substituir_arquivo_temporario(temporario, destino, tentativas=1)
