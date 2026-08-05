# ── Credentials ──────────────────────────────────────────────────────────────
# Secrets are resolved from environment variables loaded from .env.
# Add project-specific secrets below following the same pattern:
#   variable = os.getenv("VARIABLE_NAME")

import os

from app.settings.environment import load_environment

load_environment()

def check_env_variable(var: str):
    result = os.getenv(var)
    if result:
        return result
    else:
        # raise EnvironmentError(f'Variavel de ambiente {var} não foi informada no .env')
        pass

# Loading variable credentials
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
login_2tech = os.getenv("USUARIO_2TECH") or os.getenv("LOGIN2TECH")
password_2tech = os.getenv("SENHA_2TECH") or os.getenv("PASSWORD2TECH")

webhook_url = check_env_variable("WEBHOOK_URL")


def validar_credenciais_2tech() -> None:
    """Fail early with a clear message without exposing credential values."""
    missing = [
        name
        for name, value in (
            ("USUARIO_2TECH/LOGIN2TECH", login_2tech),
            ("SENHA_2TECH/PASSWORD2TECH", password_2tech),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Configuração obrigatória ausente: {', '.join(missing)}")
