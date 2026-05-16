"""Veridifi backend — FastAPI app entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.exceptions import VeridifiError
from app.routes.account import router as account_router
from app.routes.verify import router as verify_router
from app.routes.webhook import router as webhook_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.mock_inference:
        # Real model loading goes here when Abdulmalik's weights are wired in.
        # Keep this branch trivial until the .keras file exists at MODEL_PATH.
        pass
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Image-verification API. Returns AUTHENTIC / MANIPULATED / SYNTHETIC at NGN 175 per call.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(VeridifiError)
async def veridifi_error_handler(request: Request, exc: VeridifiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


app.include_router(verify_router, tags=["verify"])
app.include_router(account_router, prefix="/account", tags=["account"])
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])


@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "mode": "mock" if settings.mock_inference else "live",
    }


@app.get("/", include_in_schema=False)
async def root():
    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}
