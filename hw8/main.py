from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from routers.predict import router as predict_router
from routers.moderation import router as moderation_router
from routers.auth import router as auth_router
from errors import PredictionError
from clients.postgres import init_db_pool, close_db_pool
from clients.redis import init_redis_pool, close_redis_pool
from clients.kafka import kafka_client
from services.predict import PredictionService
from config import MODEL_PATH, SENTRY_DSN, SENTRY_ENVIRONMENT
from ml.model import load_or_train_model
from logging_config import setup_app_logging
import uvicorn
import logging

setup_app_logging()
logger = logging.getLogger(__name__)

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=SENTRY_ENVIRONMENT,
        integrations=[FastApiIntegration()],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database pool...")
    await init_db_pool()

    logger.info("Initializing Redis pool...")
    await init_redis_pool()

    logger.info("Initializing Kafka...")
    await kafka_client.start()

    logger.info(f"Loading model from {MODEL_PATH}...")
    model = load_or_train_model(MODEL_PATH)
    app.state.prediction_service = PredictionService(model=model)

    logger.info("Application started")
    yield

    logger.info("Closing Kafka...")
    await kafka_client.stop()

    logger.info("Closing Redis pool...")
    await close_redis_pool()

    logger.info("Closing database pool...")
    await close_db_pool()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Moderation service is running"}


def prediction_error_handler(request: Request, exc: PredictionError) -> JSONResponse:
    sentry_sdk.capture_exception(exc)
    return JSONResponse(status_code=500, content={'detail': str(exc)})


app.add_exception_handler(PredictionError, prediction_error_handler)
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(moderation_router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
