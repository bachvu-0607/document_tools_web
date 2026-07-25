from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.exam_variant import router as exam_variant_router
from app.api.images import router as images_router
from app.api.omr import router as omr_router
from app.api.summaries import router as summaries_router
from app.api.translations import router as translations_router
from app.core.config import settings
from app.core.auth_database import init_auth_db
from app.core.database import init_db
from app.core.omr_database import init_omr_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bang users phai co truoc, cac bang khac se tham chieu user_id toi day.
    await init_auth_db()
    # Chay 1 lan luc server khoi dong, tao bang summary_history neu chua co.
    await init_db()
    # Tao bang omr_sheets neu chua co (module OMR, tach rieng khoi summary_history).
    await init_omr_db()
    yield


# FastAPI app chinh ma uvicorn se chay.
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Cho phep frontend local o port 3000 goi API backend port 8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gan nhom endpoint health vao prefix /api, thanh /api/health.
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(documents_router, prefix=settings.api_prefix)
app.include_router(exam_variant_router, prefix=settings.api_prefix)
app.include_router(images_router, prefix=settings.api_prefix)
app.include_router(omr_router, prefix=settings.api_prefix)
app.include_router(summaries_router, prefix=settings.api_prefix)
app.include_router(translations_router, prefix=settings.api_prefix)

@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    # Trang goc don gian de biet API server da mo.
    return {
        "message": "PDF AI Summarizer API",
        "health": f"{settings.api_prefix}/health",
    }
