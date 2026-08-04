"""Indicadores de produção por vendedor, sem leitura ou escrita de arquivos."""

from __future__ import annotations

import pandas as pd


INDICADORES_COLUNAS = [
    "_vendedor_id",
    "primeira_producao",
    "ultima_producao",
    "dias_sem_producao",
    "quantidade_propostas_total",
    "quantidade_propostas_30_dias",
    "valor_producao_total",
    "valor_ultimos_30_dias",
    "valor_30_dias_anteriores",
    "valor_ultimos_90_dias",
    "media_mensal_3_meses",
    "media_mensal_6_meses",
    "meses_historico_disponiveis",
    "historico_suficiente_3_meses",
    "historico_suficiente_6_meses",
    "historico_suficiente",
    "percentual_queda",
    "queda_30d_vs_30d_anterior",
    "banco_principal_por_valor",
    "produto_principal_por_valor",
    "producao_confirmada",
    "origem_data_referencia",
    "chave_relacionamento",
]


def _principal_por_valor(grupo: pd.DataFrame, coluna: str) -> object:
    if coluna not in grupo:
        return pd.NA
    valores = grupo.loc[grupo[coluna].notna() & grupo[coluna].ne("")]
    if valores.empty:
        return pd.NA
    totais = valores.groupby(coluna, dropna=True)["valor_producao"].sum().reset_index()
    # Desempate determinístico pelo texto exibido, além do maior valor.
    return totais.sort_values(["valor_producao", coluna], ascending=[False, True]).iloc[0][coluna]


def _meses_disponiveis(primeira: pd.Timestamp, referencia: pd.Timestamp) -> int:
    diferenca_meses = (referencia.year - primeira.year) * 12 + referencia.month - primeira.month
    return max(diferenca_meses + 1, 0)


def _media_mensal(
    grupo: pd.DataFrame, referencia: pd.Timestamp, meses: int, meses_disponiveis: int
) -> object:
    if meses_disponiveis < meses:
        return pd.NA
    periodos = pd.period_range(referencia.to_period("M") - (meses - 1), periods=meses, freq="M")
    totais = (
        grupo.assign(_mes=grupo["data_referencia_producao"].dt.to_period("M"))
        .groupby("_mes")["valor_producao"]
        .sum()
        .reindex(periodos, fill_value=0.0)
    )
    return float(totais.mean())


def _producao_confirmada(grupo: pd.DataFrame) -> object:
    if "producao_validada_por_status" not in grupo:
        return pd.NA
    valores = grupo["producao_validada_por_status"].dropna()
    return bool(valores.any()) if not valores.empty else pd.NA


def _chave_relacionamento(grupo: pd.DataFrame) -> object:
    if "chave_relacionamento" not in grupo:
        return pd.NA
    chaves = grupo["chave_relacionamento"].dropna().unique().tolist()
    if not chaves:
        return pd.NA
    return chaves[0] if len(chaves) == 1 else "misto"


def _contar_propostas(grupo: pd.DataFrame) -> int:
    if "numero_proposta" not in grupo:
        return len(grupo)
    return int(grupo["numero_proposta"].nunique())


def _percentual_queda(valor_atual: float, valor_anterior: float) -> object:
    if valor_anterior <= 0:
        return pd.NA
    return ((valor_anterior - valor_atual) / valor_anterior) * 100


def calcular_indicadores_por_vendedor(
    producao_associada: pd.DataFrame, data_referencia: pd.Timestamp
) -> pd.DataFrame:
    """Resume registros relacionados em uma linha de indicadores por parceiro."""
    referencia = pd.Timestamp(data_referencia).normalize()
    base = producao_associada.dropna(subset=["_vendedor_id"]).copy()
    if base.empty:
        return pd.DataFrame(columns=INDICADORES_COLUNAS)
    base["data_referencia_producao"] = pd.to_datetime(
        base["data_referencia_producao"], errors="coerce"
    )
    base = base.dropna(subset=["data_referencia_producao"]).copy()
    if base.empty:
        return pd.DataFrame(columns=INDICADORES_COLUNAS)
    base["valor_producao"] = pd.to_numeric(base["valor_producao"], errors="coerce").fillna(0.0)
    inicio_30 = referencia - pd.Timedelta(days=30)
    inicio_60 = referencia - pd.Timedelta(days=60)
    inicio_90 = referencia - pd.Timedelta(days=90)
    linhas: list[dict[str, object]] = []
    for vendedor_id, grupo in base.groupby("_vendedor_id", sort=False):
        grupo = grupo.sort_values("data_referencia_producao")
        primeira = grupo["data_referencia_producao"].min()
        ultima = grupo["data_referencia_producao"].max()
        meses = _meses_disponiveis(primeira, referencia)
        recentes = grupo.loc[grupo["data_referencia_producao"].ge(inicio_30)]
        anteriores = grupo.loc[
            grupo["data_referencia_producao"].ge(inicio_60)
            & grupo["data_referencia_producao"].lt(inicio_30)
        ]
        valor_recente = float(recentes["valor_producao"].sum())
        valor_anterior = float(anteriores["valor_producao"].sum())
        queda = _percentual_queda(valor_recente, valor_anterior)
        linhas.append(
            {
                "_vendedor_id": vendedor_id,
                "primeira_producao": primeira,
                "ultima_producao": ultima,
                "dias_sem_producao": max((referencia - ultima).days, 0),
                "quantidade_propostas_total": _contar_propostas(grupo),
                "quantidade_propostas_30_dias": _contar_propostas(recentes),
                "valor_producao_total": float(grupo["valor_producao"].sum()),
                "valor_ultimos_30_dias": valor_recente,
                "valor_30_dias_anteriores": valor_anterior,
                "valor_ultimos_90_dias": float(
                    grupo.loc[
                        grupo["data_referencia_producao"].ge(inicio_90),
                        "valor_producao",
                    ].sum()
                ),
                "media_mensal_3_meses": _media_mensal(grupo, referencia, 3, meses),
                "media_mensal_6_meses": _media_mensal(grupo, referencia, 6, meses),
                "meses_historico_disponiveis": meses,
                "historico_suficiente_3_meses": meses >= 3,
                "historico_suficiente_6_meses": meses >= 6,
                "historico_suficiente": meses >= 3,
                "percentual_queda": queda,
                "queda_30d_vs_30d_anterior": queda,
                "banco_principal_por_valor": _principal_por_valor(grupo, "banco"),
                "produto_principal_por_valor": _principal_por_valor(grupo, "produto"),
                "producao_confirmada": _producao_confirmada(grupo),
                "origem_data_referencia": grupo.iloc[-1].get("origem_data_referencia", pd.NA),
                "chave_relacionamento": _chave_relacionamento(grupo),
            }
        )
    return pd.DataFrame(linhas, columns=INDICADORES_COLUNAS)
