# Schemas Pydantic para o domínio de desempenho esportivo.

from typing import Optional
from pydantic import BaseModel


class TemporadaDesempenho(BaseModel):
    #Desempenho esportivo do clube em uma temporada.

    ano: int

    class Config:
        extra = "allow"  # campos de competições variam por clube/ano


class DesempenhoResponse(BaseModel):
   # Resposta da rota.

    clube: str
    total: int
    anos: list[int]
    dados: list[TemporadaDesempenho]
    fonte: Optional[str] = None
