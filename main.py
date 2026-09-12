from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import corsOrigins
from routers import desempenho, diagnostico, estatisticas, financeiro, metadados, projecoes, transferencias
from services.sheetsClient import SheetsAPIError

app = FastAPI(
    title="Plataforma Analítica de Clubes de Futebol - API",
    description=(
        "Backend FastAPI consome a API, calcula indicadores financeiros e esportivos, executa o motor de regras e gera projeções de curto e médio prazo."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=corsOrigins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(SheetsAPIError)
def handleSheetsApiError(request: Request, exc: SheetsAPIError):
    return JSONResponse(status_code=exc.code, content={"detail": exc.message})

apiPrefix = "/api"
app.include_router(metadados.router, prefix=apiPrefix)
app.include_router(desempenho.router, prefix=apiPrefix)
app.include_router(financeiro.router, prefix=apiPrefix)
app.include_router(transferencias.router, prefix=apiPrefix)
app.include_router(diagnostico.router, prefix=apiPrefix)
app.include_router(projecoes.router, prefix=apiPrefix)
app.include_router(estatisticas.router, prefix=apiPrefix)


@app.get(f"{apiPrefix}/", tags=["Metadados"])
def raizApi():
    return {
        "nome": "Plataforma Analítica de Clubes de Futebol API",
    }

_frontendDist = Path(__file__).parent / "frontend" / "dist"
if _frontendDist.exists():
    app.mount("/", StaticFiles(directory=_frontendDist, html=True), name="frontend")

