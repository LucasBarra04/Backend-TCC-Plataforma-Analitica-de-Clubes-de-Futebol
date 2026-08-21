# Funções de cálculo financeiro: CAGR, médias móveis e percentis.

from statistics import median
from typing import Optional

import numpy as np


def filtrar_periodo(
    serie: dict[int, Optional[float]],
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> dict[int, Optional[float]]:

    return {
        ano: valor
        for ano, valor in serie.items()
        if (ano_inicio is None or ano >= ano_inicio)
        and (ano_fim is None or ano <= ano_fim)
    }


def calcular_cagr(
    serie: dict[int, Optional[float]], janela_anos: Optional[int] = None
) -> Optional[float]:

    # Calcula o CAGR (Compound Annual Growth Rate) de uma série histórica.
    # CAGR = (valor_final / valor_inicial) ^ (1 / n_periodos) - 1

    anos_validos = sorted(a for a, v in serie.items() if v is not None)
    if len(anos_validos) < 2:
        return None

    if janela_anos is not None:
        ano_corte = anos_validos[-1] - janela_anos
        anos_validos = [a for a in anos_validos if a >= ano_corte]
        if len(anos_validos) < 2:
            return None

    ano_inicial, ano_final = anos_validos[0], anos_validos[-1]
    valor_inicial = serie[ano_inicial]
    valor_final = serie[ano_final]
    n_periodos = ano_final - ano_inicial

    if n_periodos <= 0 or valor_inicial is None or valor_inicial <= 0:
        return None

    cagr = (valor_final / valor_inicial) ** (1 / n_periodos) - 1
    return round(cagr, 6)


def calcular_cagr_multiplas_janelas(
    serie: dict[int, Optional[float]], janelas: tuple[int, ...] = (3, 5, 8)
) -> dict[str, Optional[float]]:

    # Calcula o CAGR de uma série para múltiplas janelas de anos.
    return {f"cagr_{j}anos": calcular_cagr(serie, janela_anos=j) for j in janelas}


def calcular_media_movel(
    serie: dict[int, Optional[float]], janela: int = 3
) -> dict[int, Optional[float]]:
    
    # Calcula a média móvel de N anos para cada ponto de uma série histórica.

    anos_ordenados = sorted(serie.keys())
    resultado: dict[int, Optional[float]] = {}

    for ano in anos_ordenados:
        janela_anos = [a for a in anos_ordenados if ano - janela + 1 <= a <= ano]
        valores = [serie[a] for a in janela_anos if serie.get(a) is not None]
        resultado[ano] = round(sum(valores) / len(valores), 4) if valores else None

    return resultado


def calcular_percentis_cagr(
    serie: dict[int, Optional[float]]
) -> dict[str, Optional[float]]:

    #Calcula os percentis 25, 50 e 75 das taxas de crescimento ano-a-ano (variação percentual anual) de uma série histórica.

    #Usado como base para os três cenários de projeção de médio prazo (conservador = p25, base = p50/mediana, otimista = p75)

    anos_validos = sorted(a for a, v in serie.items() if v is not None)
    variacoes: list[float] = []

    for a_prev, a_atual in zip(anos_validos, anos_validos[1:]):
        v_prev, v_atual = serie[a_prev], serie[a_atual]
        if v_prev and v_prev > 0:
            variacoes.append((v_atual / v_prev) - 1)

    if len(variacoes) < 2:
        return {"p25": None, "p50": None, "p75": None}

    return {
        "p25": round(float(np.percentile(variacoes, 25)), 6),
        "p50": round(float(median(variacoes)), 6),
        "p75": round(float(np.percentile(variacoes, 75)), 6),
    }

def ultimo_valor_valido(serie: dict[int, Optional[float]]) -> tuple[Optional[int], Optional[float]]:

    # Retorna o (ano, valor) mais recente com dado não-nulo em uma série.

    anos_validos = sorted((a for a, v in serie.items() if v is not None), reverse=True)
    if not anos_validos:
        return None, None
    ano = anos_validos[0]
    return ano, serie[ano]
