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
from services.mqtt_subscriber import subscriber as mqtt_subscriber
from services.dose_monitor import dose_monitor

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

    # Start MQTT subscriber to listen for device telemetry/status/alerts
    import asyncio
    mqtt_subscriber.start(asyncio.get_running_loop())

    # Start dose monitor (scans for missed doses every few minutes,
    # alerts caregiver via SNS).
    dose_monitor.start()

    yield

    dose_monitor.stop()
    mqtt_subscriber.stop()
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


@app.post("/api/v1/demo/dispense")
async def demo_dispense(slot: int = 1, quantity: int = 1):
    """Quick test: send dispense command to the default device.

    Example:
      curl -X POST 'http://localhost:8000/api/v1/demo/dispense?slot=1&quantity=2'
    """
    from services.aws_iot import IoTService
    iot = IoTService()
    await iot.send_dispense_command(
        device_id=settings.DEVICE_ID,
        slot=slot,
        quantity=quantity,
    )
    return {"ok": True, "device_id": settings.DEVICE_ID, "slot": slot, "quantity": quantity}


@app.post("/api/v1/demo/ping")
async def demo_ping():
    """Ping the default device — firmware will reply with status='pong'."""
    from services.aws_iot import IoTService
    iot = IoTService()
    await iot.send_ping(settings.DEVICE_ID)
    return {"ok": True, "device_id": settings.DEVICE_ID}


@app.post("/api/v1/demo/scan-missed-doses")
async def demo_scan_missed_doses():
    """Manually trigger the missed-dose scanner (useful for demo)."""
    await dose_monitor._scan()
    return {"ok": True, "message": "Missed-dose scan completed"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
