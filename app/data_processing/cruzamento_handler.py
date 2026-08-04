"""Ponto de compatibilidade para a consolidação analítica de parceiros."""

from __future__ import annotations

from datetime import date
import logging
from pathlib import Path

import pandas as pd

from app.data_processing.consolidacao_handler import associar_producao_a_vendedores, consolidar_vendedores_producao
from app.data_processing.export_handler import exportar_excel_atomico
from app.data_processing.indicadores_handler import calcular_indicadores_por_vendedor
from app.data_processing.normalization import normalizar_codigo_vendedor, normalizar_documento
from app.data_processing.validators import garantir_dataframe_nao_vazio
from app.settings.config import PARCEIROS_CLASSIFICADOS_OUTPUT_PATH

logger = logging.getLogger(__name__)

# Interface antiga mantida para consumidores que ainda exibem essa classificação.
CLASSIFICATION_ORDER = [
    "Sem produção no período analisado", "Sem produção há 60 dias", "Sem produção há 30 dias",
    "Sem produção há 15 dias", "Produzindo normalmente",
]
FINAL_COLUMNS = [
    "codigo_vendedor", "cpf_cnpj", "nome_vendedor", "situacao_cadastral", "grupo_vendedor",
    "responsavel_comercial", "data_cadastro", "primeira_producao", "ultima_producao",
    "dias_sem_producao", "quantidade_propostas_total", "quantidade_propostas_30_dias",
    "valor_producao_total", "valor_ultimos_30_dias", "valor_30_dias_anteriores",
    "valor_ultimos_90_dias", "media_mensal_3_meses", "media_mensal_6_meses",
    "percentual_queda", "queda_30d_vs_30d_anterior", "meses_historico_disponiveis",
    "historico_suficiente_3_meses", "historico_suficiente_6_meses", "historico_suficiente",
    "banco_principal_por_valor", "produto_principal_por_valor", "producao_confirmada",
    "qualidade_dados", "classificacao_monitoramento", "chave_relacionamento",
    "origem_data_referencia", "data_atualizacao",
]


def classificar_producao(dias_sem_producao: object) -> str:
    """Classificação legada por faixas de dia; a saída nova usa a técnica."""
    if pd.isna(dias_sem_producao):
        return "Sem produção no período analisado"
    dias = int(dias_sem_producao)
    if dias < 15:
        return "Produzindo normalmente"
    if dias < 30:
        return "Sem produção há 15 dias"
    if dias < 60:
        return "Sem produção há 30 dias"
    return "Sem produção há 60 dias"


def _match_producao_a_vendedores(vendedores: pd.DataFrame, producao: pd.DataFrame) -> pd.DataFrame:
    """Compatibilidade privada: não usa mais nome como chave de relacionamento."""
    base = vendedores.reset_index(drop=True).copy()
    if "_vendedor_id" not in base:
        base["_vendedor_id"] = base.index.astype("int64")
    return associar_producao_a_vendedores(base, producao)


def resumir_producao_por_vendedor(producao_associada: pd.DataFrame) -> pd.DataFrame:
    """Resumo legado derivado dos indicadores canônicos."""
    referencia = pd.to_datetime(producao_associada.get("data_referencia_producao", producao_associada.get("data_producao")), errors="coerce").max()
    if pd.isna(referencia):
        referencia = pd.Timestamp.today().normalize()
    base = producao_associada.copy()
    if "data_referencia_producao" not in base:
        base["data_referencia_producao"] = base.get("data_producao")
    indicadores = calcular_indicadores_por_vendedor(base, referencia)
    return indicadores.rename(columns={
        "ultima_producao": "data_ultima_producao",
        "quantidade_propostas_total": "quantidade_propostas",
        "valor_producao_total": "valor_total_produzido",
    })[["_vendedor_id", "data_ultima_producao", "quantidade_propostas", "valor_total_produzido"]]


def _controle(vendedores: pd.DataFrame, producao: pd.DataFrame, metricas: dict[str, int], referencia: pd.Timestamp) -> dict[str, object]:
    datas = pd.to_datetime(producao.get("data_referencia_producao"), errors="coerce")
    return {
        "data_execucao": referencia,
        "data_referencia": referencia,
        "periodo_inicial_producao": datas.min(),
        "periodo_final_producao": datas.max(),
        "quantidade_vendedores_origem": len(vendedores),
        "quantidade_vendedores_processados": metricas["quantidade_vendedores_processados"],
        "quantidade_producoes_origem": len(producao),
        "quantidade_producoes_processadas": len(producao),
        "quantidade_parceiros_sem_producao": metricas["quantidade_parceiros_sem_producao"],
        "quantidade_parceiros_consolidados": metricas["quantidade_parceiros_consolidados"],
        "quantidade_producoes_sem_vendedor": metricas["quantidade_producoes_sem_vendedor"],
        "quantidade_datas_invalidas": int(datas.isna().sum()),
        "quantidade_documentos_invalidos": int(producao.get("cpf_cnpj", pd.Series(dtype="string")).eq("").sum()),
        "quantidade_codigos_invalidos": int(producao.get("codigo_vendedor", pd.Series(dtype="string")).eq("").sum()),
        "meses_historico_disponiveis": int(
            pd.to_numeric(metricas.get("meses_historico_disponiveis", 0), errors="coerce")
        ),
        "possui_data_pagamento": bool(producao.get("possui_data_pagamento", pd.Series(False)).any()),
        "fonte_dados": "2Tech / Gerencial Crédito",
        "versao_processamento": "2.1",
    }


def cruzar_vendedores_producao(
    caminho_vendedores: Path,
    caminho_producao: Path,
    caminho_saida: Path = PARCEIROS_CLASSIFICADOS_OUTPUT_PATH,
    data_referencia: date | None = None,
) -> Path:
    """Consolida e exporta a base para monitoramento, com aba CONTROLE."""
    vendedores = pd.read_excel(caminho_vendedores, dtype=str)
    producao = pd.read_excel(caminho_producao, dtype=str)
    garantir_dataframe_nao_vazio(vendedores, "Arquivo de vendedores para cruzamento")
    garantir_dataframe_nao_vazio(producao, "Arquivo de produção para cruzamento")
    for coluna, normalizador in (("codigo_vendedor", normalizar_codigo_vendedor), ("cpf_cnpj", normalizar_documento)):
        if coluna in vendedores:
            vendedores[coluna] = vendedores[coluna].map(normalizador)
        if coluna in producao:
            producao[coluna] = producao[coluna].map(normalizador)
    if "data_referencia_producao" not in producao:
        producao["data_referencia_producao"] = producao.get("data_producao")
    if "origem_data_referencia" not in producao:
        producao["origem_data_referencia"] = "producao"
    referencia = pd.Timestamp(data_referencia or date.today()).normalize()
    resultado, metricas = consolidar_vendedores_producao(
        vendedores, producao, referencia
    )
    nao_relacionadas = metricas.pop("producoes_nao_relacionadas")
    meses = pd.to_numeric(resultado.get("meses_historico_disponiveis"), errors="coerce")
    metricas["meses_historico_disponiveis"] = int(meses.max()) if meses.notna().any() else 0
    for coluna in FINAL_COLUMNS:
        if coluna not in resultado:
            resultado[coluna] = pd.NA
    resultado = resultado.loc[:, FINAL_COLUMNS]
    ordenacao = {
        "POTENCIAL_REATIVACAO": 0,
        "ATENCAO": 1,
        "DADOS_INSUFICIENTES": 2,
        "SEM_HISTORICO": 3,
        "CADASTRO_INATIVO": 4,
        "ATIVO": 5,
    }
    resultado = resultado.assign(_ordem=resultado["classificacao_monitoramento"].map(ordenacao).fillna(99)).sort_values("_ordem").drop(columns="_ordem")
    logger.info("Vendedores ativos cruzados: %d", len(resultado))
    for classificacao, quantidade in resultado["classificacao_monitoramento"].value_counts().items():
        logger.info("Classificação %s: %d", classificacao, quantidade)
    return exportar_excel_atomico(
        resultado,
        caminho_saida,
        "Parceiros consolidados",
        _controle(vendedores, producao, metricas, referencia),
        nao_relacionadas,
    )
