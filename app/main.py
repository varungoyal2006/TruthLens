import logging 
import sys 
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings 
from app.core.logger import setup_logging

from app.api import health, audit

setup_logging() 

logger = logging.getLogger(__name__)

app = FastAPI(
  title=settings.PROJECT_NAME, 
  description="Agentic RAG pipeline for automated video claim verification.", 
  version='1.0.0', 
  docs_url="/docs",
  redoc_url="/redoc",
)

app.add_middleware(
  CORSMiddleware, 
  allow_origins=["*"],
  allow_credentials=True, 
  allow_methods=["*"], 
  allow_headers=["*"], 
)

app.include_router(health.router, tags=["Sustem Health"])

app.include_router(audit.router, prefix=settings.API_V1_STR, tags=['Verification Core'])

logging.info("TruthLens FastAPI server initialized and ready for connections.")