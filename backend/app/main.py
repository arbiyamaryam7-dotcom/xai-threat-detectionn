"""FastAPI application entry point.  Run: uvicorn app.main:app --reload  (from backend/)"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from . import models  # noqa: F401  (registers tables)
from .config import settings
from .database import Base, SessionLocal, engine
from .routers import alerts, predict, reports, stats
from .services.predictor import ModelNotReady, get_predictor

log = logging.getLogger("xai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)       # creates tables on first start
    yield


app = FastAPI(title="XAI Cyber Threat Detection API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_methods=["*"], allow_headers=["*"])
for r in (predict.router, alerts.router, stats.router, reports.router):
    app.include_router(r, prefix="/api")


@app.exception_handler(ModelNotReady)
async def model_missing(_: Request, exc: ModelNotReady):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def db_error(_: Request, exc: SQLAlchemyError):
    log.exception("Database error")
    return JSONResponse(status_code=500, content={"detail": "Database error. Check DATABASE_URL and that PostgreSQL is running."})


@app.get("/api/health")
def health():
    status = {"api": "ok", "database": "ok", "models": "ok"}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as e:
        status["database"] = f"error: {e.__class__.__name__}"
    try:
        get_predictor(settings.anomaly_model)
    except ModelNotReady as e:
        status["models"] = str(e)
    return status
