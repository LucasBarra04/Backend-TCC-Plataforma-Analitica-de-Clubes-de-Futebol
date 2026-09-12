# Configurações globais.

import os
from dotenv import load_dotenv

load_dotenv()

sheetsApiUrl: str = os.getenv("SHEETS_API_URL")
sheetsApiTimeout: float = float(os.getenv("SHEETS_API_TIMEOUT", "15"))
sheetsApiMaxRetries: int = int(os.getenv("SHEETS_API_MAX_RETRIES", "3"))
sheetsCacheTtlSegundos: int = int(os.getenv("SHEETS_CACHE_TTL_SEGUNDOS", "180"))

clubesValidos: list[str] = ["flamengo", "palmeiras", "internacional", "sao_paulo"]

anosRecorte: list[int] = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
anoMin: int = min(anosRecorte)
anoMax: int = max(anosRecorte)

direcoesValidas: list[str] = ["saidas", "entradas"]

tiposTransferenciaValidos: list[str] = [
    "transferencia", "emprestimo", "custo_zero", "fim_emprestimo",
]

indicadoresComparaveis: list[str] = [
    "receita_bruta",
    "receita_operacional_liquida",
    "superavit_deficit",
    "ebitda",
    "resultado_financeiro",
    "passivo_total",
]

limiaresMotorRegras: dict = {
    "crescimentoReceita": {
        "direcao": "maior_melhor",
        "saudavelMin": 0.08,    
        "atencaoMin": 0.04,      
        "unidade": "percentual",
    },
    "endividamento": {
        "direcao": "menor_melhor",
        "saudavelMax": 1.5,      
        "atencaoMax": 2.5,       
        "unidade": "multiplo",
    },
    "custoFutebol": {
        "direcao": "menor_melhor",
        "saudavelMax": 0.55,     
        "atencaoMax": 0.70,      
        "unidade": "percentual",
    },
    "concentracaoReceita": {
        "direcao": "menor_melhor",
        "saudavelMax": 0.40,     
        "atencaoMax": 0.60,     
        "unidade": "percentual",
    },
}

limiaresEficienciaEsportiva: dict = {
    "direcao": "maior_melhor",
    "atencaoDesvioMax": -0.20,
    "criticoDesvioMax": -0.50,
    "unidade": "percentual_desvio",
}

corsOrigins: list[str] = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")