from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from Backend.Services.Semantics.semantic_service import (
    calcular_cotovelo,
    carregar_ultima_clusterizacao,
    clusterizar,
)

app = FastAPI(title="Observatório das Mídias Sociais")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ClusterRequest(BaseModel):
    k: int = Field(ge=2, le=50)
    start_date: date | None = None
    end_date: date | None = None
    period_mode: str = "last7"


def _validate_period(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="A data inicial deve ser anterior ou igual à data final.",
        )


def _validate_period_mode(period_mode):
    if period_mode not in {"all", "last7", "custom"}:
        raise HTTPException(
            status_code=422,
            detail="O modo do período deve ser all, last7 ou custom.",
        )


@app.get("/api/clusters/elbow")
def elbow(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    period_mode: str = Query(default="last7"),
):
    _validate_period(start_date, end_date)
    _validate_period_mode(period_mode)
    try:
        return calcular_cotovelo(start_date, end_date, period_mode)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/clusters")
def clusters(request: ClusterRequest):
    _validate_period(request.start_date, request.end_date)
    _validate_period_mode(request.period_mode)
    try:
        return clusterizar(
            request.k, request.start_date, request.end_date, request.period_mode
        )
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/api/clusters/latest")
def latest_cluster():
    try:
        resultado = carregar_ultima_clusterizacao()
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma clusterização persistida foi encontrada.",
        )
    return resultado
