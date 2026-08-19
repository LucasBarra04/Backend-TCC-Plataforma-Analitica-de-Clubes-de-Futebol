# Schemas Pydantic para o motor de regras e cards de diagnóstico.

from typing import Literal, Optional
from pydantic import BaseModel


class CardDiagnostico(BaseModel):
    # Card de alerta gerado pelo motor de regras.

    indicador: str
    valor: Optional[float]
    valor_formatado: str
    status: Literal["saudavel", "atencao", "critico", "indisponivel"]
    texto: str


class DiagnosticoResponse(BaseModel):
    # Diagnóstico completo de um clube em um ano ou período.

    clube: str
    ano_referencia: Optional[int] = None
    cards: list[CardDiagnostico]


class DiagnosticoSerieResponse(BaseModel):
    # Diagnóstico de um clube ao longo de múltiplos anos.

    clube: str
    anos: list[int]
    serie: dict[int, list[CardDiagnostico]]


class DiagnosticoComparativoResponse(BaseModel):
    # Diagnóstico comparativo dos clubes.

    ano_referencia: Optional[int] = None
    flamengo: list[CardDiagnostico]
    palmeiras: list[CardDiagnostico]
