from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from Backend.Services.Semantics.semantic_service import calcular_cotovelo, clusterizar

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


def _validate_period(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="A data inicial deve ser anterior ou igual à data final.",
        )


@app.get("/api/clusters/elbow")
def elbow(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    _validate_period(start_date, end_date)
    try:
        return calcular_cotovelo(start_date, end_date)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/clusters")
def clusters(request: ClusterRequest):
    _validate_period(request.start_date, request.end_date)
    try:
        return clusterizar(request.k, request.start_date, request.end_date)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
