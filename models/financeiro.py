# Schemas Pydantic para o domínio financeiro.

from typing import Literal, Optional
from pydantic import BaseModel, Field


class IndicadorInfo(BaseModel):
    # Dados de um indicador financeiro disponível.

    slug: str
    label: str
    secao: str
    anos_com_dados: int
    cobertura: str
    unidade: str
    comparavel_entre_clubes: bool = False
    alias_comparativo: Optional[str] = None


class IndicadoresResponse(BaseModel):
    # Resposta da rota de listagem de indicadores de um clube.

    clube: str
    total: int
    indicadores: list[IndicadorInfo]


class SerieIndicador(BaseModel):
    # Histórico para um indicador financeiro.

    clube: str
    indicador: str
    label: str
    secao: str
    unidade: str
    serie: dict[int, Optional[float]]
    anos_com_dados: list[int]
    obs: Optional[str] = None


class ValorPontual(BaseModel):
    # Valor para um indicador financeiro em um ano específico.

    clube: str
    indicador: str
    label: str
    secao: str
    unidade: str
    ano: int
    valor: Optional[float]
    obs: Optional[str] = None


class LinhaFinanceira(BaseModel):
   # Linha de dados financeiros dentro de uma seção (DRE, Balanço, Indicadores) .

    slug: str
    label: str
    unidade: str
    valores: dict[int, Optional[float]]
    obs: Optional[str] = None


class FinanceiroCompleto(BaseModel):
    # Todos os indicadores financeiros de um clube por seção.

    clube: str
    anos_recorte: list[int]
    unidade_padrao: str
    dados: dict[str, list[LinhaFinanceira]]
    nota: Optional[str] = None
    fonte: Optional[str] = None


class SnapshotAno(BaseModel):
    # Snapshot dos indicadores financeiros dO clube no ano.

    clube: str
    ano: int
    unidade: str
    dados: dict[str, dict[str, Optional[float]]]
    nota: Optional[str] = None


class ComparativoIndicador(BaseModel):
    # Indicador financeiro comparado lado a lado entre dois clubes.

    indicador: str
    alias: str
    slug_flamengo: str
    slug_palmeiras: str
    unidade: str
    anos: list[int]
    serie: dict[int, dict[Literal["flamengo", "palmeiras"], Optional[float]]]
    nota: Optional[str] = None
