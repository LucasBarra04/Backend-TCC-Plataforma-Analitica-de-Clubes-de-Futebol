# Serviço de projeções financeiras.

# Metodologia das Projeções (Tratadas como estimativas acadêmicas; longo prazo descartado por insuficiência amostral):
# Curto prazo (1 ano): Média(CAGR 3 anos, MM 3 anos) aplicada ao último valor observado.
# Médio prazo (2-3 anos): Cenários conservador/base/otimista utilizando os percentis 25, 50 e 75 das variações históricas como taxas compostas sucessivas sobre o último valor.

from typing import Optional

from models.projecao import ProjecaoCenario, ProjecaoCurtoPrazo, ProjecaoMedioPrazo
from services import calculos, sheets_client


def _serie_indicador(clube: str, indicador: str) -> dict[int, Optional[float]]:

   # Busca a série histórica de um indicador para um clube.

    # Tenta primeiro via rota comparativa (alias público); se o indicador não for comparável, cai para a rota `financeiro` usando o slug real.

    try:
        dados = sheets_client.comparativo(indicador)
        return {int(a): v.get(clube) for a, v in dados["serie"].items()}
    except Exception:
        dados = sheets_client.financeiro(clube, indicador=indicador)
        return {int(a): v for a, v in dados["serie"].items()}


def projetar_curto_prazo(clube: str, indicador: str) -> ProjecaoCurtoPrazo:
    # Gera a projeção de 1 ano de um indicador financeiro para um clube.

    # Taxa aplicada = média(CAGR 3 anos, taxa implícita da média móvel de 3 anos).
    # A taxa implícita da média móvel é calculada como (média_móvel_atual / valor_base) - 1.
   
    serie = _serie_indicador(clube, indicador)
    ano_base, valor_base = calculos.ultimo_valor_valido(serie)

    if ano_base is None or valor_base is None:
        return ProjecaoCurtoPrazo(
            indicador=indicador, clube=clube, ano_base=0, valor_base=None,
            cagr_3anos=None, media_movel_3anos=None, taxa_aplicada=None, projecao=None,
        )

    cagr_3 = calculos.calcular_cagr(serie, janela_anos=3)
    medias_moveis = calculos.calcular_media_movel(serie, janela=3)
    media_movel_atual = medias_moveis.get(ano_base)

    taxa_media_movel = (
        (media_movel_atual / valor_base) - 1
        if media_movel_atual and valor_base
        else None
    )

    taxas_disponiveis = [t for t in [cagr_3, taxa_media_movel] if t is not None]
    taxa_aplicada = round(sum(taxas_disponiveis) / len(taxas_disponiveis), 6) if taxas_disponiveis else None

    if taxa_aplicada is None:
        projecao = None
    else:
        valor_projetado = round(valor_base * (1 + taxa_aplicada), 2)
        projecao = ProjecaoCenario(
            ano=ano_base + 1,
            valor_projetado=valor_projetado,
            metodo="media_cagr3_media_movel3",
            premissas={
                "valor_base": valor_base,
                "ano_base": ano_base,
                "cagr_3anos": cagr_3,
                "taxa_media_movel_3anos": taxa_media_movel,
                "taxa_aplicada": taxa_aplicada,
            },
        )

    return ProjecaoCurtoPrazo(
        indicador=indicador,
        clube=clube,
        ano_base=ano_base,
        valor_base=valor_base,
        cagr_3anos=cagr_3,
        media_movel_3anos=media_movel_atual,
        taxa_aplicada=taxa_aplicada,
        projecao=projecao,
    )


def projetar_medio_prazo(
    clube: str, indicador: str, horizonte_anos: int = 3
) -> ProjecaoMedioPrazo:
    # Gera a projeção de médio prazo (2-3 anos) de um indicador financeiro.

    if horizonte_anos not in (2, 3):
        raise ValueError("horizonte_anos deve ser 2 ou 3.")

    serie = _serie_indicador(clube, indicador)
    ano_base, valor_base = calculos.ultimo_valor_valido(serie)
    percentis = calculos.calcular_percentis_cagr(serie)

    cenarios: dict[str, list[ProjecaoCenario]] = {
        "cenario_conservador": [],
        "cenario_base": [],
        "cenario_otimista": [],
    }

    if ano_base is None or valor_base is None:
        return ProjecaoMedioPrazo(
            indicador=indicador,
            cenario_conservador=[],
            cenario_base=[],
            cenario_otimista=[],
        )

    mapa_cenario_percentil = {
        "cenario_conservador": ("p25", percentis["p25"]),
        "cenario_base": ("p50", percentis["p50"]),
        "cenario_otimista": ("p75", percentis["p75"]),
    }

    for nome_cenario, (nome_percentil, taxa) in mapa_cenario_percentil.items():
        if taxa is None:
            continue
        valor_corrente = valor_base
        for passo in range(1, horizonte_anos + 1):
            valor_corrente = round(valor_corrente * (1 + taxa), 2)
            cenarios[nome_cenario].append(
                ProjecaoCenario(
                    ano=ano_base + passo,
                    valor_projetado=valor_corrente,
                    metodo=f"crescimento_composto_{nome_percentil}",
                    premissas={
                        "valor_base": valor_base,
                        "ano_base": ano_base,
                        "taxa_anual_aplicada": taxa,
                        "percentil": nome_percentil,
                    },
                )
            )

    return ProjecaoMedioPrazo(
        indicador=indicador,
        cenario_conservador=cenarios["cenario_conservador"],
        cenario_base=cenarios["cenario_base"],
        cenario_otimista=cenarios["cenario_otimista"],
    )
