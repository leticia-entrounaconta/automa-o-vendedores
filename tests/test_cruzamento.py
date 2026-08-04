from datetime import date

import pandas as pd

from app.data_processing.cruzamento_handler import (
    classificar_producao,
    cruzar_vendedores_producao,
    resumir_producao_por_vendedor,
)


def test_classificacao_por_dias_sem_producao() -> None:
    assert classificar_producao(5) == "Produzindo normalmente"
    assert classificar_producao(15) == "Sem produção há 15 dias"
    assert classificar_producao(29) == "Sem produção há 15 dias"
    assert classificar_producao(30) == "Sem produção há 30 dias"
    assert classificar_producao(59) == "Sem produção há 30 dias"
    assert classificar_producao(60) == "Sem produção há 60 dias"
    assert classificar_producao(pd.NA) == "Sem produção no período analisado"


def test_resumir_producao_por_vendedor() -> None:
    production = pd.DataFrame(
        {
            "_vendedor_id": [0, 0, 1],
            "data_producao": pd.to_datetime(["2026-07-01", "2026-07-05", "2026-07-04"]),
            "numero_proposta": ["A", "A", "B"],
            "valor_producao": [100.0, 100.0, 50.0],
        }
    )
    summary = resumir_producao_por_vendedor(production).set_index("_vendedor_id")
    assert summary.loc[0, "data_ultima_producao"] == pd.Timestamp("2026-07-05")
    assert summary.loc[0, "quantidade_propostas"] == 1
    assert summary.loc[1, "valor_total_produzido"] == 50.0


def test_left_join_preserves_seller_without_production(tmp_path) -> None:
    sellers_path = tmp_path / "vendedores.xlsx"
    production_path = tmp_path / "producao.xlsx"
    output_path = tmp_path / "classificados.xlsx"
    pd.DataFrame(
        {
            "codigo_vendedor": ["001", "002"],
            "nome_vendedor": ["Ana", "Bia"],
            "cpf_cnpj": ["00123456789", "00987654321"],
            "grupo_vendedor": ["Comercial", "Comercial"],
            "situacao_cadastral": ["Ativo", "Ativo"],
        }
    ).to_excel(sellers_path, index=False)
    pd.DataFrame(
        {
            "codigo_vendedor": ["001"],
            "data_producao": ["2026-07-26"],
            "numero_proposta": ["P1"],
            "valor_producao": [125.0],
        }
    ).to_excel(production_path, index=False)

    cruzar_vendedores_producao(
        sellers_path, production_path, output_path, data_referencia=date(2026, 7, 31)
    )
    result = pd.read_excel(output_path, dtype={"codigo_vendedor": str})
    assert len(result) == 2
    assert set(result["classificacao_monitoramento"]) == {
        "DADOS_INSUFICIENTES",
        "SEM_HISTORICO",
    }
    ana = result.loc[result["codigo_vendedor"] == "001"].iloc[0]
    assert ana["quantidade_propostas_total"] == 1
