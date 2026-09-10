import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available (checks backend/.env first, then root .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
ROOT_ENV_PATH = BASE_DIR.parent / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
elif ROOT_ENV_PATH.exists():
    load_dotenv(dotenv_path=ROOT_ENV_PATH)
else:
    load_dotenv()

# General Configuration
APP_NAME = "Enterprise GenAI Security Gateway"
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Database Configuration
# Use Render PostgreSQL when DATABASE_URL is provided; otherwise fall back to local SQLite for development.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///security_gateway.db")

# External LLM Configuration
# Primary Provider: "groq" (also supports "openai")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# Risk Threshold Configuration
# Action thresholds for Policy Engine
BLOCK_ON_PII = os.getenv("BLOCK_ON_PII", "True").lower() == "true"
BLOCK_ON_CREDENTIALS = os.getenv("BLOCK_ON_CREDENTIALS", "True").lower() == "true"
BLOCK_ON_SECRETS = os.getenv("BLOCK_ON_SECRETS", "True").lower() == "true"
BLOCK_ON_CONFIDENTIAL = os.getenv("BLOCK_ON_CONFIDENTIAL", "True").lower() == "true"
