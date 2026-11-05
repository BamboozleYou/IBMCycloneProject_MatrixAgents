"""Application-wide settings loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# IBM watsonx
WATSONX_API_KEY: str = os.environ.get("WATSONX_API_KEY", "")
WATSONX_URL: str = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_PROJECT_ID: str = os.environ.get("WATSONX_PROJECT_ID", "")

# Google Gemini
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

# Groq
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")

# LiteLLM fallback order
FALLBACK_MODELS: list[str] = [
    f"watsonx/ibm/granite-4-dense-8b-instruct",
    "gemini/gemini-1.5-pro",
    "groq/llama3-70b-8192",
]

# Storage paths
DB_PATH: Path = BASE_DIR / os.environ.get("DB_PATH", "costs.db")
AUDIT_DB_PATH: Path = BASE_DIR / os.environ.get("AUDIT_DB_PATH", "audit.db")
CHROMA_DB_DIR: Path = BASE_DIR / os.environ.get("CHROMA_DB_DIR", "chroma_db")
LOGS_DIR: Path = BASE_DIR / "logs"

# Misc
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

# Ensure runtime dirs exist
for _dir in (LOGS_DIR, CHROMA_DB_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
