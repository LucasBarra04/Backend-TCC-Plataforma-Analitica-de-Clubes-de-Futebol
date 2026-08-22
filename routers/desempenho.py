# Rotas de desempenho esportivo.

from typing import Optional

from fastapi import APIRouter, Depends

from routers.deps import ano_query, clube_path
from services import sheets_client

router = APIRouter(prefix="/desempenho", tags=["Desempenho Esportivo"])


@router.get("/{clube}")
def get_desempenho(
    clube: str = Depends(clube_path),
    ano: Optional[int] = Depends(ano_query),
):
    return sheets_client.desempenho(clube, ano)
