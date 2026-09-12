# Cliente HTTP para a API

import json
import threading
import time
from typing import Any, Optional

import requests
from fastapi import HTTPException

from config import sheetsApiMaxRetries, sheetsApiTimeout, sheetsApiUrl, sheetsCacheTtlSegundos


class SheetsAPIError(Exception):

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


_cache: dict[str, tuple[float, dict]] = {}
_locksPorChave: dict[str, threading.Lock] = {}
_locksGuard = threading.Lock()


def _lockDaChave(chave: str) -> threading.Lock:
    with _locksGuard:
        lock = _locksPorChave.get(chave)
        if lock is None:
            lock = threading.Lock()
            _locksPorChave[chave] = lock
        return lock


def _chaveCache(params: dict[str, Any]) -> str:
    limpos = {k: v for k, v in params.items() if v is not None}
    return json.dumps(limpos, sort_keys=True)


def limparCache() -> None:
    with _locksGuard:
        _cache.clear()
        _locksPorChave.clear()


def _get(params: dict[str, Any]) -> dict:
    chave = _chaveCache(params)

    entrada = _cache.get(chave)
    if entrada is not None and (time.monotonic() - entrada[0]) < sheetsCacheTtlSegundos:
        return entrada[1]

    with _lockDaChave(chave):
        entrada = _cache.get(chave)
        if entrada is not None and (time.monotonic() - entrada[0]) < sheetsCacheTtlSegundos:
            return entrada[1]

        dados = _buscarNaApi(params)
        _cache[chave] = (time.monotonic(), dados)
        return dados


def _buscarNaApi(params: dict[str, Any]) -> dict:
    parametrosLimpos = {k: v for k, v in params.items() if v is not None}

    ultimoErro: Optional[Exception] = None

    for _tentativa in range(1, sheetsApiMaxRetries + 1):
        try:
            resp = requests.get(sheetsApiUrl, params=parametrosLimpos, timeout=sheetsApiTimeout)
        except requests.exceptions.RequestException as exc:
            ultimoErro = exc
            continue

        if resp.status_code != 200:
            ultimoErro = RuntimeError(f"Status HTTP inesperado da API Sheets: {resp.status_code}")
            continue

        try:
            corpo = resp.json()
        except ValueError as exc:
            ultimoErro = exc
            continue

        if corpo.get("success"):
            return corpo.get("data", {})

        erro = corpo.get("error", {})
        raise SheetsAPIError(code=erro.get("code", 500), message=erro.get("message", "Erro desconhecido na API Sheets."))

    raise HTTPException(
        status_code=502,
        detail=(
            "Não foi possível obter dados da API do Google Apps Script "
            f"após {sheetsApiMaxRetries} tentativas. Detalhe: {ultimoErro}"
        ),
    )

_camposLinhaFinanceira = {
    "slug": "slug", "label": "label", "nivel": "nivel", "unidade": "unidade", "valores": "valores", "obs": "obs",
}

_camposCompeticaoDesempenho = {
    "brasileirao": "brasileirao",
    "copa_do_brasil": "copaDoBrasil",
    "copa_libertadores": "copaLibertadores",
    "sulamericana": "sulAmericana",
    "supercopa_do_brasil": "supercopaDoBrasil",
    "recopa_sulamericana": "recopaSulAmericana",
    "mundial_de_clubes_anual": "mundialDeClubesAnual",
    "copa_do_mundo_de_clubes": "copaDoMundoDeClubes",
    "campeonato_estadual": "campeonatoEstadual",
}


def _traduzirTemporada(temporada: dict) -> dict:
    traduzida = {"ano": temporada.get("ano")}
    for chaveOriginal, chaveNova in _camposCompeticaoDesempenho.items():
        if chaveOriginal in temporada:
            traduzida[chaveNova] = temporada[chaveOriginal]
    return traduzida


def _traduzirLinhaFinanceira(linha: dict) -> dict:
    traduzida = {chaveNova: linha.get(chaveOriginal) for chaveOriginal, chaveNova in _camposLinhaFinanceira.items()}
    traduzida["nivel"] = traduzida.get("nivel") or 0
    return traduzida


def _traduzirMovimentacao(mov: dict) -> dict:
    return {
        "jogador": mov.get("jogador"),
        "clube": mov.get("clube"),
        "valorMi": mov.get("valor_mi"),
        "tipo": mov.get("tipo"),
    }

def health() -> dict:
    return _get({"route": "health"})


def clubes() -> dict:
    return _get({"route": "clubes"})


def anos() -> dict:
    return _get({"route": "anos"})


def indicadores(clube: str) -> dict:
    dados = _get({"route": "indicadores", "clube": clube})
    return {
        "clube": dados["clube"],
        "total": dados["total"],
        "indicadores": [
            {
                "slug": i["slug"],
                "label": i["label"],
                "secao": i["secao"],
                "anosComDados": i["anos_com_dados"],
                "cobertura": i["cobertura"],
                "unidade": i["unidade"],
                "comparavelEntreClubes": i.get("comparavel_entre_clubes", False),
                "aliasComparativo": i.get("alias_comparativo"),
            }
            for i in dados["indicadores"]
        ],
        "nota": dados.get("nota"),
    }

def desempenho(clube: str, ano: Optional[int] = None) -> dict:
    dados = _get({"route": "desempenho", "clube": clube, "ano": ano})
    return {
        "clube": dados["clube"],
        "total": dados["total"],
        "anos": dados["anos"],
        "dados": [_traduzirTemporada(t) for t in dados["dados"]],
        "fonte": dados.get("fonte"),
    }

def financeiro(clube: str, ano: Optional[int] = None, indicador: Optional[str] = None) -> dict:
    dados = _get({"route": "financeiro", "clube": clube, "ano": ano, "indicador": indicador})

    if indicador and ano:
        return {
            "clube": dados["clube"], "indicador": dados["indicador"], "label": dados["label"],
            "secao": dados["secao"], "unidade": dados["unidade"], "ano": dados["ano"],
            "valor": dados["valor"], "obs": dados.get("obs"),
        }

    if indicador and not ano:
        return {
            "clube": dados["clube"], "indicador": dados["indicador"], "label": dados["label"],
            "secao": dados["secao"], "unidade": dados["unidade"], "serie": dados["serie"],
            "anosComDados": dados["anos_com_dados"], "obs": dados.get("obs"),
        }

    if ano and not indicador:
        return {
            "clube": dados["clube"], "ano": dados["ano"], "unidade": dados["unidade"],
            "dados": dados["dados"], "nota": dados.get("nota"),
        }

    return {
        "clube": dados["clube"],
        "anosRecorte": dados["anos_recorte"],
        "unidadePadrao": dados["unidade_padrao"],
        "dados": {secao: [_traduzirLinhaFinanceira(l) for l in linhas] for secao, linhas in dados["dados"].items()},
        "nota": dados.get("nota"),
        "fonte": dados.get("fonte"),
    }


def comparativo(indicador: str, ano: Optional[int] = None, clubesFiltro: Optional[list[str]] = None) -> dict:
    params = {"route": "comparativo", "indicador": indicador, "ano": ano}
    if clubesFiltro:
        params["clubes"] = ",".join(clubesFiltro)
    dados = _get(params)
    return {
        "indicador": dados["indicador"],
        "alias": dados["alias"],
        "clubes": dados["clubes"],
        "slugsPorClube": dados["slugs_por_clube"],
        "unidade": dados["unidade"],
        "anos": dados["anos"],
        "serie": dados["serie"],
        "nota": dados.get("nota"),
    }

def transferencias(
    clube: str, ano: Optional[int] = None, direcao: Optional[str] = None, tipo: Optional[str] = None
) -> dict:
    dados = _get({"route": "transferencias", "clube": clube, "ano": ano, "direcao": direcao, "tipo": tipo})

    transferenciasTraduzidas = {}
    for anoChave, bloco in dados["transferencias"].items():
        blocoTraduzido = {}
        if "saidas" in bloco:
            blocoTraduzido["saidas"] = [_traduzirMovimentacao(m) for m in bloco["saidas"]]
        if "entradas" in bloco:
            blocoTraduzido["entradas"] = [_traduzirMovimentacao(m) for m in bloco["entradas"]]
        transferenciasTraduzidas[anoChave] = blocoTraduzido

    return {
        "clube": dados["clube"],
        "anos": dados["anos"],
        "direcao": dados["direcao"],
        "tipoFiltro": dados.get("tipo_filtro"),
        "transferencias": transferenciasTraduzidas,
        "totais": {
            "saidasMi": dados["totais"]["saidas_mi"],
            "entradasMi": dados["totais"]["entradas_mi"],
            "saldoMi": dados["totais"]["saldo_mi"],
        },
        "unidade": dados["unidade"],
        "fonte": dados.get("fonte"),
    }


def saldoTransferencias(clube: str, ano: Optional[int] = None) -> dict:
    dados = _get({"route": "saldo_transferencias", "clube": clube, "ano": ano})
    return {
        "clube": dados["clube"],
        "anos": dados["anos"],
        "serie": {
            anoChave: {
                "saidasMi": v["saidas_mi"], "entradasMi": v["entradas_mi"], "saldoMi": v["saldo_mi"],
                "nSaidas": v["n_saidas"], "nEntradas": v["n_entradas"],
            }
            for anoChave, v in dados["serie"].items()
        },
        "total": {
            "saidasMi": dados["total"]["saidas_mi"],
            "entradasMi": dados["total"]["entradas_mi"],
            "saldoMi": dados["total"]["saldo_mi"],
        },
        "unidade": dados["unidade"],
        "fonte": dados.get("fonte"),
    }