"""Verifica somente a autenticação Microsoft Graph, sem Selenium ou upload."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.integrations.sharepoint import (
    ENV_PATH,
    MS_CLIENT_ID,
    MS_CLIENT_SECRET,
    MS_TENANT_ID,
    _obter_token,
)


def main() -> None:
    """Exibe somente metadados seguros e confirma a obtenção do token."""

    print(f".env: {ENV_PATH}")
    print(f"Tenant: {MS_TENANT_ID}")
    print(f"Client ID: {MS_CLIENT_ID}")
    print(f"Secret preenchido: {bool(MS_CLIENT_SECRET)}")
    print(f"Tamanho do secret: {len(MS_CLIENT_SECRET)}")

    token = _obter_token()

    print("Token obtido com sucesso.")
    print(f"Tamanho do token: {len(token)}")


if __name__ == "__main__":
    main()
