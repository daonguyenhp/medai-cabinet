from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ScheduleBase(BaseModel):
    medication_id: str
    times: List[str] = Field(..., description="Danh sách giờ uống, e.g. ['08:00', '20:00']")
    days_of_week: List[str] = Field(
        default=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    )
    dosage_count: int = Field(1, ge=1)
    instructions: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True
    reminder_enabled: bool = True
    caregiver_notify: bool = False


class ScheduleCreate(ScheduleBase):
    user_id: str


class ScheduleResponse(ScheduleBase):
    schedule_id: str
    user_id: str
    medication_name: Optional[str] = None
    unit: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class DoseHistoryCreate(BaseModel):
    user_id: str
    medication_id: str
    schedule_id: Optional[str] = None
    scheduled_time: Optional[str] = None
    taken_time: Optional[str] = None
    status: Literal["taken", "missed", "late", "skipped"] = "taken"
    dosage_count: int = 1
    pill_count_verified: Optional[bool] = None
    notes: Optional[str] = None


class DoseHistoryResponse(DoseHistoryCreate):
    history_id: str
    medication_name: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
