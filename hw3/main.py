from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.predict import router as predict_router
from errors import PredictionError
from clients.postgres import init_db_pool, close_db_pool
from services.predict import PredictionService
from config import MODEL_PATH
import uvicorn
import logging
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hw2'))
from model import load_or_train_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@dataclass
class AppState:
    prediction_service: PredictionService


_app_state: Optional[AppState] = None


def get_app_state() -> AppState:
    if _app_state is None:
        raise RuntimeError("App state not initialized")
    return _app_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _app_state
    
    logger.info("Initializing database pool...")
    await init_db_pool()
    
    logger.info(f"Loading model from {MODEL_PATH}...")
    model = load_or_train_model(MODEL_PATH)
    
    _app_state = AppState(prediction_service=PredictionService(model=model))
    
    logger.info("Application started")
    yield
    
    logger.info("Closing database pool...")
    await close_db_pool()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Moderation service is running"}


def prediction_error_handler(request: Request, exc: PredictionError) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': str(exc)})


app.add_exception_handler(PredictionError, prediction_error_handler)
app.include_router(predict_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
