from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, HTTPException, Request

from risk_platform.config import Settings
from risk_platform.domain import Event, Prediction
from risk_platform.inference.service import RiskScorer
from risk_platform.models.bundle import ModelBundle


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    if settings.model_path.exists():
        app.state.scorer = RiskScorer(ModelBundle.load(settings.model_path), settings)
    yield


app = FastAPI(title="Real-Time Risk Intelligence API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health(request: Request) -> dict[str, str]:
    return {"status": "healthy" if hasattr(request.app.state, "scorer") else "not_ready"}


@app.post("/v1/score", response_model=Prediction)
def score(event: Event, request: Request) -> Prediction:
    scorer = cast(RiskScorer | None, getattr(request.app.state, "scorer", None))
    if scorer is None:
        raise HTTPException(503, "model artifact is not loaded; run training first")
    return scorer.score(event)
