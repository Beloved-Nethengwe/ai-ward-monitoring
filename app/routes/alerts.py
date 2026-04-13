from fastapi import APIRouter

from app.models import Alert
from app.services import list_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[Alert])
def get_alerts(patient_id: str | None = None) -> list[Alert]:
    return list_alerts(patient_id=patient_id)