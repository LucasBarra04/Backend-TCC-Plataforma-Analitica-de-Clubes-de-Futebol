# Dependências FastAPI para validar parâmetros comuns entre a rotas.

from typing import Optional

from fastapi import HTTPException, Path, Query

from config import (
    ANO_MAX,
    ANO_MIN,
    CLUBES_VALIDOS,
    DIRECOES_VALIDAS,
    TIPOS_TRANSFERENCIA_VALIDOS,
)

def clube_path(
    clube: str = Path(..., description="Clube: flamengo ou palmeiras")
) -> str:
    clube_norm = clube.lower().strip()
    if clube_norm not in CLUBES_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f'Clube "{clube}" inválido. Use: {" | ".join(CLUBES_VALIDOS)}',
        )
    return clube_norm

def ano_query(
    ano: Optional[int] = Query(
        None, description=f"Ano específico ({ANO_MIN}-{ANO_MAX})"
    )
) -> Optional[int]:
    if ano is not None and not (ANO_MIN <= ano <= ANO_MAX):
        raise HTTPException(
            status_code=404,
            detail=f"Ano {ano} fora do recorte {ANO_MIN}-{ANO_MAX}.",
        )
    return ano

def direcao_query(
    direcao: Optional[str] = Query(
        None, description='Direção: "saidas" ou "entradas"'
    )
) -> Optional[str]:
    if direcao is not None and direcao.lower() not in DIRECOES_VALIDAS:
        raise HTTPException(
            status_code=400,
            detail=f'Parâmetro "direcao" deve ser um de: {" | ".join(DIRECOES_VALIDAS)}',
        )
    return direcao.lower() if direcao else None

def tipo_transferencia_query(
    tipo: Optional[str] = Query(None, description="Tipo de movimentação")
) -> Optional[str]:
    if tipo is not None and tipo.lower() not in TIPOS_TRANSFERENCIA_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f'Parâmetro "tipo" deve ser um de: {" | ".join(TIPOS_TRANSFERENCIA_VALIDOS)}',
        )
    return tipo.lower() if tipo else None
