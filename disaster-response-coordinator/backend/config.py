"""
Configuration module for AI Disaster Response Coordinator.
All settings loaded from environment variables via python-dotenv.
"""
import os
import logging
from dotenv import load_dotenv

# Ensure we load .env from the backend directory regardless of cwd
basedir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(basedir, ".env")
env_example_path = os.path.join(basedir, ".env.example")

if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
elif os.path.exists(env_example_path):
    load_dotenv(env_example_path, override=True)
else:
    load_dotenv(override=True)

# ── Gemini / AI ──────────────────────────────────────────────────────────────
_raw_key = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEY: str = _raw_key.strip().strip('"').strip("'")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
GEMINI_TIMEOUT: int = int(os.getenv("GEMINI_TIMEOUT", "30"))
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

# ── Flask ─────────────────────────────────────────────────────────────────────
FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# ── CORS ──────────────────────────────────────────────────────────────────────
_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
CORS_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///disaster_response.db")

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

# ── Agent retry / timeout ────────────────────────────────────────────────────
MAX_AGENT_RETRIES: int = int(os.getenv("MAX_AGENT_RETRIES", "2"))
AGENT_RETRY_DELAY: float = float(os.getenv("AGENT_RETRY_DELAY", "1.0"))

# ── Pagination ────────────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

# ── Limits ────────────────────────────────────────────────────────────────────
MAX_REPORT_LENGTH: int = int(os.getenv("MAX_REPORT_LENGTH", "4000"))
