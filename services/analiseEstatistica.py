# Teste de associação estatística entre financeiro e desempenho.

from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor
from scipy import stats as scipyStats

from config import anosRecorte
from models.estatistica import PontoPainel, ResultadoCorrelacao, TesteHipotese
from services import pontuacaoFederacoes, sheetsClient
from services.motorRegras import buscarLinhaDespesaOperacional, extrairFontesReceita
ProvedorVariavel = Callable[[str], dict[int, Optional[float]]]

anosRecorteCbf = pontuacaoFederacoes.anosRecorteCbf
anosRecorteConmebol = pontuacaoFederacoes.anosRecorteConmebol

def _normalizar(texto: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# Provedores de variável financeira

def _serieReceitaBruta(clube: str) -> dict[int, Optional[float]]:
    dados = sheetsClient.comparativo("receita_bruta")
    return {int(a): v.get(clube) for a, v in dados["serie"].items()}


def _seriePassivoTotal(clube: str) -> dict[int, Optional[float]]:
    dados = sheetsClient.comparativo("passivo_total")
    return {int(a): v.get(clube) for a, v in dados["serie"].items()}


def _serieDespesaOperacional(clube: str) -> dict[int, Optional[float]]:
    linha = buscarLinhaDespesaOperacional(clube)
    if linha is None:
        return {}
    return {int(a): (abs(v) if v is not None else None) for a, v in linha["valores"].items()}


def _serieGastoContratacoes(clube: str) -> dict[int, Optional[float]]:
    dados = sheetsClient.transferencias(clube)
    serie = {}
    for anoChave, bloco in dados["transferencias"].items():
        entradas = bloco.get("entradas", [])
        serie[int(anoChave)] = round(sum(m["valorMi"] for m in entradas), 2) if entradas else 0.0
    return serie


def _serieEndividamento(clube: str) -> dict[int, Optional[float]]:
    passivo = _seriePassivoTotal(clube)
    receita = _serieReceitaBruta(clube)
    return {
        ano: round(passivo[ano] / receita[ano], 4)
        for ano in passivo
        if passivo.get(ano) is not None and receita.get(ano)
    }


def _serieCustoFutebol(clube: str) -> dict[int, Optional[float]]:
    despesa = _serieDespesaOperacional(clube)
    receita = _serieReceitaBruta(clube)
    return {
        ano: round(despesa[ano] / receita[ano], 4)
        for ano in despesa
        if despesa.get(ano) is not None and receita.get(ano)
    }


def _serieConcentracaoReceita(clube: str) -> dict[int, Optional[float]]:
    dados = sheetsClient.financeiro(clube)
    dre = dados.get("dados", {}).get("dre", [])
    fontes = extrairFontesReceita(dre)
    if len(fontes) < 2:
        return {}

    serie = {}
    for ano in anosRecorte:
        valores = [l["valores"].get(str(ano), l["valores"].get(ano)) for l in fontes]
        validos = [v for v in valores if v is not None and v > 0]
        if len(validos) < 2:
            continue
        serie[ano] = round(max(validos) / sum(validos), 4)
    return serie


# Provedores de variável esportiva

def _serieEsportiva(clube: str, federacao: str) -> dict[int, Optional[float]]:
    dadosDesempenho = sheetsClient.desempenho(clube)
    temporadas = dadosDesempenho.get("dados", [])
    serieFn = pontuacaoFederacoes.serieHistoricaCbf if federacao == "cbf" else pontuacaoFederacoes.serieHistoricaConmebol
    serieFederacao = serieFn(temporadas)
    return {ano: v["bruta"] for ano, v in serieFederacao["serie"].items() if v["bruta"] is not None}


def _serieCbf(clube: str) -> dict[int, Optional[float]]:
    return _serieEsportiva(clube, "cbf")


def _serieConmebol(clube: str) -> dict[int, Optional[float]]:
    return _serieEsportiva(clube, "conmebol")


# Variáveis

variaveisFinanceiras: dict[str, ProvedorVariavel] = {
    "receitaBruta": _serieReceitaBruta,
    "despesaOperacional": _serieDespesaOperacional,
    "gastoContratacoes": _serieGastoContratacoes,
    "endividamento": _serieEndividamento,
    "custoFutebol": _serieCustoFutebol,
    "concentracaoReceita": _serieConcentracaoReceita,
}

variaveisEsportivas: dict[str, ProvedorVariavel] = {
    "pontuacaoCbfBruta": _serieCbf,
    "pontuacaoConmebolBruta": _serieConmebol,
}

variaveisDisponiveis: dict[str, ProvedorVariavel] = {**variaveisFinanceiras, **variaveisEsportivas}

_janelaPorVariavelEsportiva = {"pontuacaoCbfBruta": anosRecorteCbf, "pontuacaoConmebolBruta": anosRecorteConmebol}


# Painel e cálculo de correlação

def montarPainel(variavelX: str, variavelY: str, clubes: Optional[list[str]] = None) -> list[PontoPainel]:
    from config import clubesValidos

    if variavelX not in variaveisDisponiveis:
        raise ValueError(f'Variável X "{variavelX}" desconhecida. Disponíveis: {", ".join(variaveisDisponiveis)}')
    if variavelY not in variaveisDisponiveis:
        raise ValueError(f'Variável Y "{variavelY}" desconhecida. Disponíveis: {", ".join(variaveisDisponiveis)}')

    clubesAlvo = clubes or clubesValidos
    janela = _janelaPorVariavelEsportiva.get(variavelY) or _janelaPorVariavelEsportiva.get(variavelX) or anosRecorte

    providerX, providerY = variaveisDisponiveis[variavelX], variaveisDisponiveis[variavelY]
    pontos: list[PontoPainel] = []

    for clube in clubesAlvo:
        serieX, serieY = providerX(clube), providerY(clube)
        for ano in janela:
            x, y = serieX.get(ano), serieY.get(ano)
            if x is not None and y is not None:
                pontos.append(PontoPainel(clube=clube, ano=ano, x=float(x), y=float(y)))

    return pontos


def _classificarForca(r: Optional[float]) -> Optional[str]:
    if r is None:
        return None
    abs_r = abs(r)
    if abs_r < 0.10:
        return "desprezivel"
    if abs_r < 0.30:
        return "fraca"
    if abs_r < 0.50:
        return "moderada"
    if abs_r < 0.70:
        return "forte"
    return "muito_forte"


def calcularCorrelacao(variavelX: str, variavelY: str, clubes: Optional[list[str]] = None) -> ResultadoCorrelacao:
    painel = montarPainel(variavelX, variavelY, clubes)
    n = len(painel)

    if n < 4:
        return ResultadoCorrelacao(
            variavelX=variavelX, variavelY=variavelY, n=n,
            pearsonR=None, pearsonP=None, spearmanR=None, spearmanP=None, forcaAssociacao=None,
            painel=painel, nota=f"Apenas {n} observações pareadas — insuficiente para calcular correlação (mínimo 4).",
        )

    xs = [p.x for p in painel]
    ys = [p.y for p in painel]

    try:
        pearson = scipyStats.pearsonr(xs, ys)
        pearsonR, pearsonP = round(float(pearson.statistic), 4), round(float(pearson.pvalue), 4)
    except Exception:
        pearsonR, pearsonP = None, None

    try:
        spearman = scipyStats.spearmanr(xs, ys)
        spearmanR, spearmanP = round(float(spearman.statistic), 4), round(float(spearman.pvalue), 4)
    except Exception:
        spearmanR, spearmanP = None, None

    nota = (
        f"N={n}, amostra pequena (painel clube×ano de {len(clubes or []) or 4} clubes) — "
        "interpretar significância com cautela; resultado é correlacional, não causal."
    )

    return ResultadoCorrelacao(
        variavelX=variavelX, variavelY=variavelY, n=n,
        pearsonR=pearsonR, pearsonP=pearsonP, spearmanR=spearmanR, spearmanP=spearmanP,
        forcaAssociacao=_classificarForca(pearsonR), painel=painel, nota=nota,
    )


# Testes Hipóste 1, Hipótese 2 e Hipótese 3

_paresVolumeH1H2 = [
    ("gastoContratacoes", "pontuacaoCbfBruta"), ("gastoContratacoes", "pontuacaoConmebolBruta"),
    ("despesaOperacional", "pontuacaoCbfBruta"), ("despesaOperacional", "pontuacaoConmebolBruta"),
    ("receitaBruta", "pontuacaoCbfBruta"), ("receitaBruta", "pontuacaoConmebolBruta"),
]

_paresQualidadeH3 = [
    ("endividamento", "pontuacaoCbfBruta"), ("endividamento", "pontuacaoConmebolBruta"),
    ("custoFutebol", "pontuacaoCbfBruta"), ("custoFutebol", "pontuacaoConmebolBruta"),
    ("concentracaoReceita", "pontuacaoCbfBruta"), ("concentracaoReceita", "pontuacaoConmebolBruta"),
]


def rodarBateriaHipoteses(clubes: Optional[list[str]] = None) -> list[TesteHipotese]:
    testeVolume = TesteHipotese(
        hipotese="Hipótese 1 e Hipótese 2: Volume de recurso financeiro",
        descricao=(
            "Hipótese 1: não existe associação significativa entre recurso financeiro aplicado e desempenho esportivo. Hipótese 2: existe associação significativa. As mesmas correlações abaixo (volume financeiro × score esportivo bruto) informam qual hipótese os dados sustentam melhor, não são testes independentes."
        ),
        resultados=[calcularCorrelacao(x, y, clubes) for x, y in _paresVolumeH1H2],
    )

    testeQualidade = TesteHipotese(
        hipotese="Hipótese 3: Qualidade e controle do gasto",
        descricao=(
            "O que explica desempenho não é o volume de recurso, e sim a qualidade e controle do gasto (endividamento, concentração de receita, custo do futebol). Nas 3 variáveis abaixo, valor MAIOR representa pior controle financeiro, uma correlação negativa consistente com o score esportivo (mais controle => melhor desempenho) sustentaria Hipótese 3."
        ),
        resultados=[calcularCorrelacao(x, y, clubes) for x, y in _paresQualidadeH3],
    )

    return [testeVolume, testeQualidade]