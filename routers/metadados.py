# Rotas de metadados: health check, clubes e anos do recorte.

from fastapi import APIRouter

from services import sheets_client

router = APIRouter(tags=["Metadados"])


@router.get("/health")
def get_health():
    # Confere se o backend e a API estão operando.
    dados_sheets = sheets_client.health()
    return {
        "status": "ok",
        "backend": "fastapi",
        "sheets_api": dados_sheets,
    }


@router.get("/clubes")
def get_clubes():
    # Lista os clubes disponíveis.
    return sheets_client.clubes()


@router.get("/anos")
def get_anos():
    # Lista os anos do recorte temporal.
    return sheets_client.anos()
