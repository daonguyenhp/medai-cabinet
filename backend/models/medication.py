from pydantic import BaseModel, Field
from typing import Optional, Literal


class MedicationBase(BaseModel):
    name: str = Field(..., description="Tên thuốc")
    generic_name: Optional[str] = Field(None, description="Tên hoạt chất")
    medication_type: Literal["pill", "syrup", "eyedrop", "injection", "cream", "other"] = "pill"
    compartment: int = Field(..., ge=1, le=3, description="Ngăn chứa (1-3)")
    stock_count: int = Field(0, ge=0)
    unit: str = Field("viên", description="Đơn vị")
    dosage_strength: Optional[str] = None
    manufacturer: Optional[str] = None
    expiry_date: Optional[str] = None
    opened_date: Optional[str] = None
    post_opening_days: Optional[int] = None
    storage_instructions: Optional[str] = None
    notes: Optional[str] = None
    low_stock_threshold: int = Field(5, ge=0)


class MedicationCreate(MedicationBase):
    user_id: str


class MedicationUpdate(MedicationBase):
    user_id: Optional[str] = None
    name: Optional[str] = None
    compartment: Optional[int] = None
    stock_count: Optional[int] = None


class MedicationResponse(MedicationBase):
    medication_id: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expiry_status: Optional[str] = None
    days_until_expiry: Optional[int] = None
    effective_expiry_date: Optional[str] = None
    warning_message: Optional[str] = None

    class Config:
        from_attributes = True


class DispenseRequest(BaseModel):
    medication_id: str
    quantity: int = Field(1, ge=1)
