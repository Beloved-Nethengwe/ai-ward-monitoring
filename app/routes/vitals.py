from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models import SimulateVitalsRequest, VitalReading
from app.services import (
    create_alert_if_needed,
    get_latest_vital,
    get_patient,
    list_vitals,
    save_vital_reading,
)
from app.simulator import build_next_vitals

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.get("/{patient_id}", response_model=list[VitalReading])
def get_vitals(patient_id: str) -> list[VitalReading]:
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return list_vitals(patient_id)


@router.get("/{patient_id}/latest", response_model=VitalReading)
def get_latest_patient_vital(patient_id: str) -> VitalReading:
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vital = get_latest_vital(patient_id)
    if not vital:
        raise HTTPException(status_code=404, detail="No vitals found for patient")

    return vital


@router.post("/{patient_id}/simulate")
def simulate_vitals(patient_id: str, payload: SimulateVitalsRequest | None = None) -> dict:
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    trend = payload.trend if payload else None
    previous = get_latest_vital(patient_id)

    vital = build_next_vitals(
        patient_id=patient_id,
        previous=previous,
        trend=trend,
    )
    vital.timestamp = datetime.utcnow()

    saved_vital = save_vital_reading(vital)
    alert = create_alert_if_needed(saved_vital)

    return {
        "vital": saved_vital,
        "alert": alert,
    }