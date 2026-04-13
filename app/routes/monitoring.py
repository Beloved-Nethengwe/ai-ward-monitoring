from fastapi import APIRouter, HTTPException

from app.models import MonitoringSession, StartMonitoringRequest
from app.services import (
    get_patient,
    list_monitoring_sessions,
    start_monitoring,
    stop_monitoring,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("", response_model=list[MonitoringSession])
def get_monitoring_sessions() -> list[MonitoringSession]:
    return list_monitoring_sessions()


@router.post("/{patient_id}/start", response_model=MonitoringSession)
def start_patient_monitoring(
    patient_id: str,
    payload: StartMonitoringRequest,
) -> MonitoringSession:
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return start_monitoring(
        patient_id=patient_id,
        trend=payload.trend,
        interval_seconds=payload.interval_seconds,
    )


@router.post("/{patient_id}/stop")
def stop_patient_monitoring(patient_id: str) -> dict[str, str]:
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    stopped = stop_monitoring(patient_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="Monitoring session not found")

    return {"message": f"Monitoring stopped for {patient_id}"}