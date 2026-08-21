# Motor de regras: avalia 5 indicadores críticos para gerar os Cards de Diagnóstico:

# 1. Crescimento de receita: CAGR (3 anos) da `receita_bruta`.
# 2. Endividamento: `passivo_total` / `receita_bruta` (utilizando os dados mais recentes de cada).
# 3. Custo do futebol: Busca label com "despesa" e "operacional" na DRE. Retorna "indisponivel" se não achar.

import re
import unicodedata
from typing import Optional

from config import LIMIARES_MOTOR_REGRAS
from models.diagnostico import CardDiagnostico
from services import calculos, sheets_client


# Utilitários de texto

def _normalizar(texto: str) -> str:

    # Nomraliza o texto tirando caixa alta, acentos etc.
   
    nfkd = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower()


# Card genérico

def _card(
    indicador: str,
    valor: Optional[float],
    status: str,
    texto: str,
    formato: str = "percentual",
) -> CardDiagnostico:
    
    # Monta um CardDiagnostico formatando o valor de acordo com sua unidade.

    if valor is None:
        valor_formatado = "N/D"
    elif formato == "percentual":
        valor_formatado = f"{valor * 100:.1f}%"
    elif formato == "multiplo":
        valor_formatado = f"{valor:.2f}x"
    else:
        valor_formatado = f"{valor:.1f}"

    return CardDiagnostico(
        indicador=indicador,
        valor=valor,
        valor_formatado=valor_formatado,
        status=status,
        texto=texto,
    )


# 1. Crescimento de receita

def avaliar_crescimento_receita(clube: str, ano_fim: Optional[int] = None) -> CardDiagnostico:

    limiares = LIMIARES_MOTOR_REGRAS["crescimento_receita"]
    dados = sheets_client.comparativo("receita_bruta")
    serie_bruta = {int(ano): vals.get(clube) for ano, vals in dados["serie"].items()}
    serie = calculos.filtrar_periodo(serie_bruta, ano_fim=ano_fim)

    cagr = calculos.calcular_cagr(serie, janela_anos=3)

    if cagr is None:
        return _card(
            "crescimento_receita", None, "indisponivel",
            "Dados insuficientes para calcular o CAGR de 3 anos da receita bruta.",
        )

    if cagr > limiares["saudavel_min"]:
        status, texto = "saudavel", (
            f"Receita bruta cresceu {cagr*100:.1f}% a.a. (CAGR 3 anos), "
            "acima do limiar saudável de 8% a.a."
        )
    elif cagr >= limiares["atencao_min"]:
        status, texto = "atencao", (
            f"Receita bruta cresceu {cagr*100:.1f}% a.a. (CAGR 3 anos), "
            "em faixa de atenção (4%–8% a.a.)."
        )
    else:
        status, texto = "critico", (
            f"Receita bruta cresceu apenas {cagr*100:.1f}% a.a. (CAGR 3 anos), "
            "abaixo do limiar crítico de 4% a.a."
        )

    return _card("crescimento_receita", cagr, status, texto, formato="percentual")


# 2. Endividamento

def avaliar_endividamento(clube: str, ano: Optional[int] = None) -> CardDiagnostico:

    limiares = LIMIARES_MOTOR_REGRAS["endividamento"]

    passivo_dados = sheets_client.comparativo("passivo_total")
    receita_dados = sheets_client.comparativo("receita_bruta")

    serie_passivo = {int(a): v.get(clube) for a, v in passivo_dados["serie"].items()}
    serie_receita = {int(a): v.get(clube) for a, v in receita_dados["serie"].items()}

    if ano:
        ano_passivo, passivo = ano, serie_passivo.get(ano)
        ano_receita, receita = ano, serie_receita.get(ano)
    else:
        ano_passivo, passivo = calculos.ultimo_valor_valido(serie_passivo)
        ano_receita, receita = calculos.ultimo_valor_valido(serie_receita)

    if passivo is None or not receita:
        return _card(
            "endividamento", None, "indisponivel",
            "Dados insuficientes de Passivo Total ou Receita Bruta para calcular o endividamento.",
        )

    razao = round(passivo / receita, 4)
    ano_ref = ano_passivo if ano_passivo == ano_receita else min(a for a in [ano_passivo, ano_receita] if a)

    if razao < limiares["saudavel_max"]:
        status, texto = "saudavel", (
            f"Passivo Total equivale a {razao:.2f}x a Receita Bruta ({ano_ref}), "
            "abaixo do limiar saudável de 1,5x."
        )
    elif razao <= limiares["atencao_max"]:
        status, texto = "atencao", (
            f"Passivo Total equivale a {razao:.2f}x a Receita Bruta ({ano_ref}), "
            "em faixa de atenção (1,5x–2,5x)."
        )
    else:
        status, texto = "critico", (
            f"Passivo Total equivale a {razao:.2f}x a Receita Bruta ({ano_ref}), "
            "acima do limiar crítico de 2,5x."
        )

    return _card("endividamento", razao, status, texto, formato="multiplo")


# 3. Custo do futebol

def _buscar_linha_dre(clube: str, *palavras_chave: str) -> Optional[dict]:
    
    # Busca, na seção DRE do financeiro de um clube, a primeira linha que label tenha todas as palavras-chave.

    dados = sheets_client.financeiro(clube)
    dre = dados.get("dados", {}).get("dre", [])
    for linha in dre:
        label_norm = _normalizar(linha["label"])
        if all(_normalizar(p) in label_norm for p in palavras_chave):
            return linha
    return None


def avaliar_custo_futebol(clube: str, ano: Optional[int] = None) -> CardDiagnostico:
    """Avalia a razão Despesas Operacionais / Receita Bruta do clube."""
    limiares = LIMIARES_MOTOR_REGRAS["custo_futebol"]

    linha_despesas = _buscar_linha_dre(clube, "despesa", "operacional")

    if linha_despesas is None:
        return _card(
            "custo_futebol", None, "indisponivel",
            "Linha de Despesas Operacionais não identificada na DRE do clube.",
        )

    receita_dados = sheets_client.comparativo("receita_bruta")
    serie_receita = {int(a): v.get(clube) for a, v in receita_dados["serie"].items()}
    serie_despesas = {int(a): v for a, v in linha_despesas["valores"].items()}

    if ano:
        despesa, receita = serie_despesas.get(ano), serie_receita.get(ano)
        ano_ref = ano
    else:
        ano_ref, despesa = calculos.ultimo_valor_valido(serie_despesas)
        receita = serie_receita.get(ano_ref) if ano_ref else None

    if despesa is None or not receita:
        return _card(
            "custo_futebol", None, "indisponivel",
            "Dados insuficientes de Despesas Operacionais ou Receita Bruta.",
        )

    razao = round(abs(despesa) / receita, 4)

    if razao < limiares["saudavel_max"]:
        status, texto = "saudavel", (
            f"Despesas Operacionais consomem {razao*100:.1f}% da Receita Bruta ({ano_ref}), "
            "abaixo do limiar saudável de 55%."
        )
    elif razao <= limiares["atencao_max"]:
        status, texto = "atencao", (
            f"Despesas Operacionais consomem {razao*100:.1f}% da Receita Bruta ({ano_ref}), "
            "em faixa de atenção (55%–70%)."
        )
    else:
        status, texto = "critico", (
            f"Despesas Operacionais consomem {razao*100:.1f}% da Receita Bruta ({ano_ref}), "
            "acima do limiar crítico de 70%."
        )

    return _card("custo_futebol", razao, status, texto, formato="percentual")


