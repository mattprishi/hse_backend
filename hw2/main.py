from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.predict import router as predict_router, set_model
from errors import PredictionError
from model import load_or_train_model
import uvicorn
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    use_mlflow = os.getenv("USE_MLFLOW", "false").lower() == "true"
    
    if use_mlflow:
        logger.info("Loading model from MLflow")
        try:
            from mlflow_example import load_model_from_mlflow
            model = load_model_from_mlflow()
        except Exception as e:
            logger.error(f"Failed to load model from MLflow: {e}")
            logger.info("Falling back to local model")
            model = load_or_train_model("model.pkl")
    else:
        model = load_or_train_model("model.pkl")
    
    set_model(model)
    yield


app = FastAPI(lifespan=lifespan)


def prediction_error_handler(
    request: Request,
    exc: PredictionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={'detail': str(exc)},
    )


app.add_exception_handler(PredictionError, prediction_error_handler)
app.include_router(predict_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
