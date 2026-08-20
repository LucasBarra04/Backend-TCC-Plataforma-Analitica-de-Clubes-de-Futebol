# Schemas Pydantic para projeções financeiras de curto e médio prazo.

from typing import Optional
from pydantic import BaseModel


class ProjecaoCenario(BaseModel):
    # Um ponto de projeção (ano + valor) dentro de um cenário.

    ano: int
    valor_projetado: float
    metodo: str
    premissas: dict


class ProjecaoCurtoPrazo(BaseModel):
    # Projeção de 1 ano para um indicador, baseada em CAGR + média móvel."""

    indicador: str
    clube: str
    ano_base: int
    valor_base: Optional[float]
    cagr_3anos: Optional[float]
    media_movel_3anos: Optional[float]
    taxa_aplicada: Optional[float]
    projecao: Optional[ProjecaoCenario]


class ProjecaoMedioPrazo(BaseModel):
    # Projeção de 2 a 3 anos para um indicador, com três cenários.

    indicador: str
    cenario_conservador: list[ProjecaoCenario]
    cenario_base: list[ProjecaoCenario]
    cenario_otimista: list[ProjecaoCenario]


class ProjecaoComparativoResponse(BaseModel):
    # Projeções de comparação entre dois clubes para um indicador.

    indicador: str
    flamengo: ProjecaoMedioPrazo
    palmeiras: ProjecaoMedioPrazo
