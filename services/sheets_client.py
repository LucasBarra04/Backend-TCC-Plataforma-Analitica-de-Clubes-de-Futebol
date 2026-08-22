# Cliente HTTP para a API do Google Apps Script.

# Único ponto do backend que utiliza `requests` contra a API da planilha.
# Encapsula as chamadas GET e gerencia timeouts, erros de rede e o envelope { success, data | error }.

from typing import Any, Optional

import requests
from fastapi import HTTPException

from config import SHEETS_API_MAX_RETRIES, SHEETS_API_TIMEOUT, SHEETS_API_URL


class SheetsAPIError(Exception):
    # Erro originado na API

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _get(params: dict[str, Any]) -> dict:
    # Executa uma requisição GET à API com retry simples.
    # Remove parâmetros None para não poluir a query string.
    clean_params = {k: v for k, v in params.items() if v is not None}

    ultimo_erro: Optional[Exception] = None

    for tentativa in range(1, SHEETS_API_MAX_RETRIES + 1):
        try:
            resp = requests.get(
                SHEETS_API_URL, params=clean_params, timeout=SHEETS_API_TIMEOUT
            )
        except requests.exceptions.Timeout as exc:
            ultimo_erro = exc
            continue
        except requests.exceptions.RequestException as exc:
            ultimo_erro = exc
            continue

        # A API do Apps Script sempre responde 200, mesmo em erro de negócio
        # (o código de erro real vem no envelope JSON).
        if resp.status_code != 200:
            ultimo_erro = RuntimeError(
                f"Status HTTP inesperado da API Sheets: {resp.status_code}"
            )
            continue

        try:
            body = resp.json()
        except ValueError as exc:
            ultimo_erro = exc
            continue

        if body.get("success"):
            return body.get("data", {})

        erro = body.get("error", {})
        raise SheetsAPIError(
            code=erro.get("code", 500),
            message=erro.get("message", "Erro desconhecido na API Sheets."),
        )

    # Todas as tentativas falharam por motivo de rede/parsing.
    raise HTTPException(
        status_code=502,
        detail=(
            "Não foi possível obter dados da API do Google Apps Script "
            f"após {SHEETS_API_MAX_RETRIES} tentativas. "
            f"Detalhe: {ultimo_erro}"
        ),
    )


def _params_periodo(ano: Optional[int], ano_inicio: Optional[int], ano_fim: Optional[int]) -> dict:

    # Normaliza parâmetros de período. Como a API recebe apenas `ano` pontual,
    # o recorte `ano_inicio/ano_fim` é aplicado no backend sobre a série completa (via `filtrar_periodo()`).

    return {"ano": ano} if ano else {}


# Metadados

def health() -> dict:
    return _get({"route": "health"})


def clubes() -> dict:
    return _get({"route": "clubes"})


def anos() -> dict:
    return _get({"route": "anos"})


def indicadores(clube: str) -> dict:
    return _get({"route": "indicadores", "clube": clube})


# Desempenho esportivo

def desempenho(clube: str, ano: Optional[int] = None) -> dict:
    return _get({"route": "desempenho", "clube": clube, "ano": ano})


# Financeiro

def financeiro(
    clube: str, ano: Optional[int] = None, indicador: Optional[str] = None
) -> dict:
    return _get(
        {"route": "financeiro", "clube": clube, "ano": ano, "indicador": indicador}
    )


def comparativo(indicador: str, ano: Optional[int] = None) -> dict:
    return _get({"route": "comparativo", "indicador": indicador, "ano": ano})


# Transferências

def transferencias(
    clube: str,
    ano: Optional[int] = None,
    direcao: Optional[str] = None,
    tipo: Optional[str] = None,
) -> dict:
    return _get(
        {
            "route": "transferencias",
            "clube": clube,
            "ano": ano,
            "direcao": direcao,
            "tipo": tipo,
        }
    )


def saldo_transferencias(clube: str, ano: Optional[int] = None) -> dict:
    return _get({"route": "saldo_transferencias", "clube": clube, "ano": ano})
