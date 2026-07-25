import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
load_dotenv()

# Doc danh sach frontend duoc phep goi backend.
def _get_cors_origins() -> list[str]:
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    # Apps
    app_name: str = os.getenv("APP_NAME", "PDF AI Summarizer API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    cors_origins: list[str] = field(default_factory=_get_cors_origins)

    #PDF
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "50"))
    upload_dir: str = os.getenv("UPLOAD_DIR", "../data/uploads")

    #OMR
    omr_upload_dir: str = os.getenv("OMR_UPLOAD_DIR", "../data/omr_uploads")

    #exam_variant
    exam_variant_dir: str = os.getenv("EXAM_VARIANT_DIR", "../data/exam_variants")


    #openai
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    #db
    database_path: str = os.getenv("DATABASE_URL", "../data/database/app.sqlite3")

    #auth
    # Khoa bi mat dung de ky/kiem tra JWT - PHAI dat gia tri rieng, khac mac dinh
    # nay khi len production (Railway), neu khong ai cung ky gia duoc token.
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-only-change-me")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24 * 7)))  # mac dinh 7 ngay
# Tao object settings dung chung cho toan backend.
settings = Settings()

