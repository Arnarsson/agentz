"""
Main FastAPI application module.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.routers.agents import router as agents_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router

# Configure logging
logger.add(
    "logs/agentz.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configured based on environment in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting {settings.APP_NAME}")
    # Initialize any required services here

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info(f"Shutting down {settings.APP_NAME}")
    # Cleanup any resources here 