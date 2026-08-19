
# Configurações globais da aplicação.

import os
from dotenv import load_dotenv

load_dotenv()

# API externa

SHEETS_API_URL: str = os.getenv(
    "SHEETS_API_URL",
)

# Timeout
SHEETS_API_TIMEOUT: float = float(os.getenv("SHEETS_API_TIMEOUT", "15"))

# Número de tentativas
SHEETS_API_MAX_RETRIES: int = int(os.getenv("SHEETS_API_MAX_RETRIES", "3"))


CLUBES_VALIDOS: list[str] = ["flamengo", "palmeiras"]

ANOS_RECORTE: list[int] = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

ANO_MIN: int = min(ANOS_RECORTE)
ANO_MAX: int = max(ANOS_RECORTE)

DIRECOES_VALIDAS: list[str] = ["saidas", "entradas"]

TIPOS_TRANSFERENCIA_VALIDOS: list[str] = [
    "transferencia",
    "emprestimo",
    "custo_zero",
    "fim_emprestimo",
]

# Indicadores comparáveis entre clubes 
INDICADORES_COMPARAVEIS: list[str] = [
    "receita_bruta",
    "receita_operacional_liquida",
    "superavit_deficit",
    "ebitda",
    "resultado_financeiro",
    "passivo_total",
]

# Motor de regras: limiares dos 5 indicadores
# Cada indicador possui limites que definem as faixas saudável / atenção / crítico.

LIMIARES_MOTOR_REGRAS: dict = {
    "crescimento_receita": {
        "direcao": "maior_melhor",
        "saudavel_min": 0.08,       # > 8% a.a.
        "atencao_min": 0.04,        # 4% - 8%
        "unidade": "percentual",
    },
    "endividamento": {
        "direcao": "menor_melhor",
        "saudavel_max": 1.5,        # < 1,5x
        "atencao_max": 2.5,         # 1,5x - 2,5x
        "unidade": "multiplo",
    },
    "custo_futebol": {
        "direcao": "menor_melhor",
        "saudavel_max": 0.55,       # < 55%
        "atencao_max": 0.70,        # 55% - 70%
        "unidade": "percentual",
    },
    "concentracao_receita": {
        "direcao": "menor_melhor",
        "saudavel_max": 0.40,       # < 40%
        "atencao_max": 0.60,        # 40% - 60%
        "unidade": "percentual",
    },
    "eficiencia_esportiva": {
        "direcao": "maior_melhor",  # score acima da média é melhor
        "atencao_desvio_max": -0.20,   # até 20% abaixo da média = atenção
        "critico_desvio_max": -0.50,   # acima de 20% abaixo (i.e. <= -20%) já é atenção;
        # > 50% abaixo da média = crítico
        "unidade": "percentual_desvio",
    },
}

CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
