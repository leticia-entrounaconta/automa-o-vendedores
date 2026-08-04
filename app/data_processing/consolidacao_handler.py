"""Relacionamento controlado e consolidação de vendedores e produção."""

from __future__ import annotations

import logging

import pandas as pd

from app.data_processing.indicadores_handler import calcular_indicadores_por_vendedor
from app.data_processing.normalization import normalizar_codigo_vendedor, normalizar_documento, normalizar_status
from app.settings.config import DIAS_ATENCAO, DIAS_REATIVACAO

logger = logging.getLogger(__name__)


def _mapa_chave_unica(vendedores: pd.DataFrame, coluna: str, normalizador) -> pd.Series:
    if coluna not in vendedores:
        return pd.Series(dtype="Int64")
    chaves = vendedores[coluna].map(normalizador)
    chaves = chaves.loc[chaves.ne("")]
    chaves = chaves.loc[~chaves.duplicated(keep=False)]
    return pd.Series(chaves.index.to_list(), index=chaves.to_list(), dtype="Int64")


def associar_producao_a_vendedores(vendedores: pd.DataFrame, producao: pd.DataFrame) -> pd.DataFrame:
    """Relaciona por código e CPF único, bloqueando conflito entre as chaves."""
    resultado = producao.copy()
    mapa_codigo = _mapa_chave_unica(vendedores, "codigo_vendedor", normalizar_codigo_vendedor)
    mapa_documento = _mapa_chave_unica(vendedores, "cpf_cnpj", normalizar_documento)
    codigo = resultado.get("codigo_vendedor", pd.Series("", index=resultado.index)).map(normalizar_codigo_vendedor)
    documento = resultado.get("cpf_cnpj", pd.Series("", index=resultado.index)).map(normalizar_documento)
    vendedor_por_codigo = codigo.map(mapa_codigo)
    vendedor_por_documento = documento.map(mapa_documento)
    conflito = vendedor_por_codigo.notna() & vendedor_por_documento.notna() & vendedor_por_codigo.ne(vendedor_por_documento)
    resultado["_vendedor_id"] = pd.Series(pd.NA, index=resultado.index, dtype="Int64")
    resultado["chave_relacionamento"] = pd.Series("nao_relacionado", index=resultado.index, dtype="string")
    resultado["motivo_nao_relacionamento"] = pd.Series(pd.NA, index=resultado.index, dtype="string")

    por_codigo = vendedor_por_codigo.notna() & ~conflito
    por_documento = vendedor_por_codigo.isna() & vendedor_por_documento.notna() & ~conflito
    resultado.loc[por_codigo, "_vendedor_id"] = vendedor_por_codigo.loc[por_codigo].astype("Int64")
    resultado.loc[por_codigo, "chave_relacionamento"] = "codigo_vendedor"
    resultado.loc[por_documento, "_vendedor_id"] = vendedor_por_documento.loc[por_documento].astype("Int64")
    resultado.loc[por_documento, "chave_relacionamento"] = "cpf_cnpj"
    resultado.loc[conflito, "motivo_nao_relacionamento"] = "conflito_codigo_documento"
    sem_chaves = codigo.eq("") & documento.eq("")
    resultado.loc[sem_chaves, "motivo_nao_relacionamento"] = "chave_ausente"
    sem_correspondencia = resultado["_vendedor_id"].isna() & resultado["motivo_nao_relacionamento"].isna()
    resultado.loc[sem_correspondencia, "motivo_nao_relacionamento"] = "vendedor_nao_encontrado"
    logger.info(
        "Relacionamentos | codigo=%d | cpf_cnpj=%d | conflitos=%d | não_relacionados=%d",
        int(por_codigo.sum()), int(por_documento.sum()), int(conflito.sum()), int(resultado["_vendedor_id"].isna().sum()),
    )
    return resultado


def obter_producoes_nao_relacionadas(producao_associada: pd.DataFrame) -> pd.DataFrame:
    """Prepara a auditoria das propostas que não podem entrar no consolidado."""
    colunas = [
        "codigo_vendedor", "cpf_cnpj", "nome_vendedor", "numero_proposta",
        "data_referencia_producao", "valor_producao", "motivo_nao_relacionamento",
    ]
    resultado = producao_associada.loc[producao_associada["_vendedor_id"].isna()].copy()
    for coluna in colunas:
        if coluna not in resultado:
            resultado[coluna] = pd.NA
    return resultado.loc[:, colunas]


def _verdadeiro(valor: object) -> bool:
    return False if pd.isna(valor) else bool(valor)


def _qualidade_dados(linha: pd.Series) -> str:
    if pd.isna(linha.get("ultima_producao")):
        return "INSUFICIENTE"
    if _verdadeiro(linha.get("historico_suficiente_6_meses")):
        return "COMPLETA"
    if _verdadeiro(linha.get("historico_suficiente_3_meses")):
        return "PARCIAL"
    return "INSUFICIENTE"


def _classificar_monitoramento(linha: pd.Series) -> str:
    if normalizar_status(linha.get("situacao_cadastral")) != "ATIVO":
        return "CADASTRO_INATIVO"
    if pd.isna(linha.get("ultima_producao")):
        return "SEM_HISTORICO"
    if not _verdadeiro(linha.get("historico_suficiente_3_meses")):
        return "DADOS_INSUFICIENTES"
    dias = int(linha["dias_sem_producao"])
    if dias < DIAS_ATENCAO:
        return "ATIVO"
    if dias < DIAS_REATIVACAO:
        return "ATENCAO"
    return "POTENCIAL_REATIVACAO"


def consolidar_vendedores_producao(
    vendedores: pd.DataFrame, producao: pd.DataFrame, data_referencia: pd.Timestamp
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Entrega uma linha por vendedor, métricas e a auditoria não relacionada."""
    base = vendedores.reset_index(drop=True).copy()
    base["_vendedor_id"] = base.index.astype("int64")
    associados = associar_producao_a_vendedores(base, producao)
    nao_relacionadas = obter_producoes_nao_relacionadas(associados)
    indicadores = calcular_indicadores_por_vendedor(associados, pd.Timestamp(data_referencia))
    resultado = base.merge(indicadores, how="left", on="_vendedor_id", validate="one_to_one")
    for coluna in ("quantidade_propostas_total", "quantidade_propostas_30_dias"):
        resultado[coluna] = resultado[coluna].fillna(0).astype(int)
    for coluna in (
        "valor_producao_total", "valor_ultimos_30_dias", "valor_30_dias_anteriores", "valor_ultimos_90_dias",
    ):
        resultado[coluna] = resultado[coluna].fillna(0.0)
    resultado["dias_sem_producao"] = resultado["dias_sem_producao"].astype("Int64")
    resultado["qualidade_dados"] = resultado.apply(_qualidade_dados, axis=1)
    resultado["classificacao_monitoramento"] = resultado.apply(_classificar_monitoramento, axis=1)
    resultado["data_atualizacao"] = pd.Timestamp(data_referencia).normalize()
    metricas = {
        "quantidade_producoes_sem_vendedor": len(nao_relacionadas),
        "quantidade_parceiros_sem_producao": int(resultado["ultima_producao"].isna().sum()),
        "quantidade_vendedores_processados": len(resultado),
        "quantidade_parceiros_consolidados": len(resultado),
        "producoes_nao_relacionadas": nao_relacionadas,
    }
    logger.info("Parceiros consolidados: %d", len(resultado))
    return resultado, metricas
