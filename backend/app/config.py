import os
from pathlib import Path

from dotenv import load_dotenv

_load_dirs = [Path.cwd(), Path(__file__).resolve().parent.parent.parent]
for d in _load_dirs:
    env_path = d / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./civisense.db",
)

_UPSTAGE_BASE_RAW = os.getenv("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1/solar").strip()
UPSTAGE_BASE_URL: str = (
    "https://api.upstage.ai/v1/solar"
    if "/v2" in _UPSTAGE_BASE_RAW
    else _UPSTAGE_BASE_RAW or "https://api.upstage.ai/v1/solar"
)
UPSTAGE_API_KEY: str = (os.getenv("UPSTAGE_API_KEY") or "").strip()
UPSTAGE_CHAT_MODEL: str = os.getenv("UPSTAGE_CHAT_MODEL", "solar-pro")

EMBEDDING_API_KEY: str = (
    (os.getenv("EMBEDDING_API_KEY") or os.getenv("UPSTAGE_API_KEY") or "").strip()
)
EMBEDDING_BASE_URL: str = os.getenv(
    "EMBEDDING_BASE_URL",
    "https://api.upstage.ai/v1/solar",
)
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "solar-embedding-1-large")
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "complaint_cases")

BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")


def validate_config() -> None:
    if not UPSTAGE_API_KEY:
        raise ValueError(
            "UPSTAGE_API_KEY is required. Set it in .env or environment."
        )
