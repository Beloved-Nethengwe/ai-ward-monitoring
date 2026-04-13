from fastapi import APIRouter, HTTPException

from app.services import get_patient_handover, get_patient

router = APIRouter(prefix="/handover", tags=["handover"])


@router.get("/{patient_id}")
def get_handover(patient_id: str) -> dict:
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    handover = get_patient_handover(patient_id)
    if handover is None:
        raise HTTPException(status_code=404, detail="Handover could not be generated")

    return handover