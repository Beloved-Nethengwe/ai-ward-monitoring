from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    surname: str = Field(..., min_length=1)
    ward: str = Field(..., min_length=1)
    bed: str = Field(..., min_length=1)
    assigned_nurse: str = Field(..., min_length=1)
    admission_reason: str = Field(..., min_length=1)
    surgeries: List[str] = Field(default_factory=list)
    notes: str = Field(default="")


class Patient(PatientCreate):
    id: str
    created_at: datetime


class  VitalReading(BaseModel):
    patient_id: str
    timestamp: datetime | None = None
    heart_rate: int
    respiratory_rate: int
    temperature: float
    systolic_bp: int
    diastolic_bp: int
    oxygen_saturation: int


class VitalEvaluation(BaseModel):
    severity: Severity
    issues: List[str] = Field(default_factory=list)


class Alert(BaseModel):
    id: str
    patient_id: str
    timestamp: datetime
    severity: Severity
    issues: List[str] = Field(default_factory=list)
    summary: str


class SimulateVitalsRequest(BaseModel):
    trend: Optional[str] = None


class MonitoringSession(BaseModel):
    patient_id: str
    active: bool = True
    trend: Optional[str] = None
    interval_seconds: int = 10
    started_at: datetime


class StartMonitoringRequest(BaseModel):
    trend: Optional[str] = None
    interval_seconds: int = Field(default=10, ge=2, le=300)


class PatientLatestStatus(BaseModel):
    patient: Patient
    latest_vital: Optional[VitalReading] = None
    latest_alert: Optional[Alert] = None
    current_severity: Severity = Severity.NORMAL