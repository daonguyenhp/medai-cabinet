"""
MedAI Cabinet - FastAPI Backend
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import os
from contextlib import asynccontextmanager

from config import settings
from routers import medications, schedules, devices, ai_triage, alerts, dashboard, iot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MedAI Cabinet API starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    yield
    logger.info("MedAI Cabinet API shutting down...")


app = FastAPI(
    title="MedAI Cabinet API",
    description="Intelligent Vision System for Home Medication Safety",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(medications.router, prefix="/api/v1/medications", tags=["medications"])
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(ai_triage.router, prefix="/api/v1/ai-triage", tags=["ai-triage"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(iot.router, prefix="/api/v1/iot", tags=["iot"])


@app.get("/")
async def root():
    return {"message": "MedAI Cabinet API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
