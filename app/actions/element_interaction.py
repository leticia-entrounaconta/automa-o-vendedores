def export_vendedores_ativos():
    """Backward-compatible name for the active seller export."""
    from app.actions.vendedores import exportar_vendedores_ativos

    return exportar_vendedores_ativos()
