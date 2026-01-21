from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.predict import router as predict_router
from errors import PredictionError
import uvicorn


app = FastAPI()


def prediction_error_handler(
    request: Request,
    exc: PredictionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={'detail': str(exc)},
    )


app.add_exception_handler(PredictionError, prediction_error_handler)
app.include_router(predict_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


