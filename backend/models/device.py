from pydantic import BaseModel, Field
from typing import Optional, List


class CompartmentStatus(BaseModel):
    compartment_id: int
    is_open: bool = False
    medication_id: Optional[str] = None


class DeviceTelemetry(BaseModel):
    device_id: str
    timestamp: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    battery_level: Optional[int] = None
    wifi_rssi: Optional[int] = None
    firmware_version: Optional[str] = None
    uptime_seconds: Optional[int] = None
    free_heap: Optional[int] = None
    compartment_status: Optional[List[CompartmentStatus]] = None


class DeviceCommand(BaseModel):
    device_id: str
    command_type: str
    payload: Optional[dict] = None


class DispenseCommand(BaseModel):
    compartment: int = Field(..., ge=1, le=3)
    quantity: int = Field(1, ge=1)
    medication_id: Optional[str] = None
