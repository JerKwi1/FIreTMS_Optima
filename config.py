
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    FIRETMS_URL: str = os.getenv("FIRETMS_URL", "http://localhost:8000/firetms")
    FIRETMS_TOKEN: str = os.getenv("FIRETMS_TOKEN", "dev-firetms-token")
    OPTIMA_URL: str = os.getenv("OPTIMA_URL", "http://localhost:8000/optima")
    OPTIMA_TOKEN: str = os.getenv("OPTIMA_TOKEN", "dev-optima-token")

    CONCURRENCY: int = int(os.getenv("CONCURRENCY", "10"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "50"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    RETRIES: int = int(os.getenv("RETRIES", "6"))
    SINCE_TS: str = os.getenv("SINCE_TS", "2025-01-01T00:00:00Z")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    SYNC_DB: str = os.getenv("SYNC_DB", "sync_state.sqlite")

settings = Settings()
