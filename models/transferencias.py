# Schemas Pydantic para o domínio de transferências de atletas.

from typing import Literal, Optional
from pydantic import BaseModel


class Movimentacao(BaseModel):
    # Uma movimentação individual de atleta (saída ou entrada).

    jogador: str
    clube: Optional[str] = None
    valor_mi: float
    tipo: Optional[str] = None


class BlocoAno(BaseModel):
    # Movimentações de um ano específico, separadas por direção.

    saidas: Optional[list[Movimentacao]] = None
    entradas: Optional[list[Movimentacao]] = None


class TotaisTransferencias(BaseModel):
    # Totais agregados de saídas, entradas e saldo.

    saidas_mi: float
    entradas_mi: float
    saldo_mi: float


class TransferenciasResponse(BaseModel):
    # Resposta da rota de transferências de um clube.

    clube: str
    anos: list[int]
    direcao: str
    tipo_filtro: Optional[str] = None
    transferencias: dict[int, BlocoAno]
    totais: TotaisTransferencias
    unidade: str
    fonte: Optional[str] = None


class SaldoAno(BaseModel):
    # Saldo de transferências no ano selecionado.

    saidas_mi: float
    entradas_mi: float
    saldo_mi: float
    n_saidas: int
    n_entradas: int


class SaldoTransferenciasResponse(BaseModel):
    # Resposta da rota de saldo anual de transferências.

    clube: str
    anos: list[int]
    serie: dict[int, SaldoAno]
    total: TotaisTransferencias
    unidade: str
    fonte: Optional[str] = None
