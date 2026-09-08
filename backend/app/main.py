# isort: skip_file
import logging
import os
import sys
from pathlib import Path

# Support running this file directly with: python app/main.py
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

os.environ.setdefault("BLIS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.config import APP_NAME
from app.database.db import init_db

# Configure clean logging format for terminal debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title=APP_NAME,
    description="Enterprise GenAI Security Gateway MVP - Final Year Capstone Project",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite default dev server is http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for seamless development and testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Run database table creation on backend startup."""
    logger.info("Starting Enterprise GenAI Security Gateway Backend...")
    init_db()
    logger.info("Backend Gateway initialized and ready to process requests.")


@app.get("/")
def root():
    return {
        "status": "online",
        "service": APP_NAME,
        "message": "Enterprise GenAI Security Gateway API is running smoothly."
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "gateway": "active",
        "version": "1.0.0"
    }


# Include API Routers
app.include_router(chat_router)
app.include_router(admin_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
