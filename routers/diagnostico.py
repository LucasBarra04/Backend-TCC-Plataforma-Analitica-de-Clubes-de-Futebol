# Rotas de diagnóstico por clube.

from typing import Optional

from fastapi import APIRouter, Depends

from config import CLUBES_VALIDOS
from models.diagnostico import (
    DiagnosticoComparativoResponse,
    DiagnosticoResponse,
)
from routers.deps import ano_query, clube_path
from services import motor_regras

router = APIRouter(prefix="/diagnostico", tags=["Motor de Regras"])


@router.get("/{clube}", response_model=DiagnosticoResponse)
def get_diagnostico(
    clube: str = Depends(clube_path),
    ano: Optional[int] = Depends(ano_query),
):
    
    # Gera os 5 cards de diagnóstico do motor de regras de um clube.

    cards = motor_regras.gerar_diagnostico(clube, ano)
    return DiagnosticoResponse(clube=clube, ano_referencia=ano, cards=cards)


@router.get("", response_model=DiagnosticoComparativoResponse)
def get_diagnostico_comparativo(ano: Optional[int] = Depends(ano_query)):
    """Gera os cards de diagnóstico dos dois clubes lado a lado."""
    diagnosticos = {c: motor_regras.gerar_diagnostico(c, ano) for c in CLUBES_VALIDOS}
    return DiagnosticoComparativoResponse(
        ano_referencia=ano,
        flamengo=diagnosticos["flamengo"],
        palmeiras=diagnosticos["palmeiras"],
    )
