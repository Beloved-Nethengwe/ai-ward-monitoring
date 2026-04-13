from fastapi import APIRouter, HTTPException

from app.models import Patient, PatientCreate, PatientLatestStatus
from app.services import (
    create_patient,
    get_patient,
    get_patient_status,
    list_all_patient_statuses,
    list_patients,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=Patient)
def add_patient(payload: PatientCreate) -> Patient:
    return create_patient(payload)


@router.get("", response_model=list[Patient])
def get_patients() -> list[Patient]:
    return list_patients()


@router.get("/status", response_model=list[PatientLatestStatus])
def get_all_patient_statuses() -> list[PatientLatestStatus]:
    return list_all_patient_statuses()


@router.get("/{patient_id}", response_model=Patient)
def get_patient_by_id(patient_id: str) -> Patient:
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/{patient_id}/status", response_model=PatientLatestStatus)
def get_patient_current_status(patient_id: str) -> PatientLatestStatus:
    status = get_patient_status(patient_id)
    if not status:
        raise HTTPException(status_code=404, detail="Patient not found")
    return status