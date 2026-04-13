from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.ai_service import format_alert_summary_text, generate_handover_summary, get_ai_alert_summary
from app.models import (
    Alert,
    MonitoringSession,
    Patient,
    PatientCreate,
    PatientLatestStatus,
    Severity,
    VitalReading,
)
from app.rules import evaluate_vitals
from app.storage import (
    ALERTS_FILE,
    MONITORING_FILE,
    PATIENTS_FILE,
    VITALS_FILE,
    read_json,
    write_json,
)


def create_patient(payload: PatientCreate) -> Patient:
    patient = Patient(
        id=f"patient_{uuid4().hex[:8]}",
        created_at=datetime.utcnow(),
        **payload.model_dump(),
    )

    patients = read_json(PATIENTS_FILE)
    patients.append(patient.model_dump(mode="json"))
    write_json(PATIENTS_FILE, patients)

    return patient


def list_patients() -> list[Patient]:
    return [Patient(**row) for row in read_json(PATIENTS_FILE)]


def get_patient(patient_id: str) -> Patient | None:
    for row in read_json(PATIENTS_FILE):
        if row["id"] == patient_id:
            return Patient(**row)
    return None


def save_vital_reading(vital: VitalReading) -> VitalReading:
    vitals = read_json(VITALS_FILE)
    vitals.append(vital.model_dump(mode="json"))
    write_json(VITALS_FILE, vitals)
    return vital


def list_vitals(patient_id: str) -> list[VitalReading]:
    rows = [row for row in read_json(VITALS_FILE) if row["patient_id"] == patient_id]
    return [VitalReading(**row) for row in rows]


def get_recent_vitals(patient_id: str, limit: int = 5) -> list[VitalReading]:
    vitals = list_vitals(patient_id)
    vitals = sorted(
        [v for v in vitals if v.timestamp is not None],
        key=lambda x: x.timestamp,
    )
    return vitals[-limit:]


def get_latest_vital(patient_id: str) -> VitalReading | None:
    vitals = list_vitals(patient_id)
    if not vitals:
        return None
    return sorted(
        [v for v in vitals if v.timestamp is not None],
        key=lambda x: x.timestamp,
    )[-1]


def get_latest_alert(patient_id: str) -> Alert | None:
    alerts = [alert for alert in list_alerts(patient_id) if alert.patient_id == patient_id]
    if not alerts:
        return None
    return sorted(
        [a for a in alerts if a.timestamp is not None],
        key=lambda x: x.timestamp,
    )[-1]


def should_create_new_alert(patient_id: str, severity: Severity, issues: list[str]) -> bool:
    latest_alert = get_latest_alert(patient_id)

    if latest_alert is None:
        return True

    recent_window = datetime.utcnow() - timedelta(minutes=5)

    if latest_alert.timestamp < recent_window:
        return True

    if latest_alert.severity != severity:
        return True

    if sorted(latest_alert.issues) != sorted(issues):
        return True

    return False


def create_alert_if_needed(vital: VitalReading) -> Alert | None:
    evaluation = evaluate_vitals(vital)

    if evaluation.severity == Severity.NORMAL:
        return None

    patient = get_patient(vital.patient_id)
    if not patient:
        return None

    if not should_create_new_alert(vital.patient_id, evaluation.severity, evaluation.issues):
        return None

    recent_vitals = get_recent_vitals(vital.patient_id, limit=5)
    ai_summary_data = get_ai_alert_summary(
        patient=patient,
        latest_vital=vital,
        recent_vitals=recent_vitals,
        issues=evaluation.issues,
    )

    alert = Alert(
        id=f"alert_{uuid4().hex[:8]}",
        patient_id=vital.patient_id,
        timestamp=datetime.utcnow(),
        severity=evaluation.severity,
        issues=evaluation.issues,
        summary=format_alert_summary_text(ai_summary_data),
    )

    alerts = read_json(ALERTS_FILE)
    alerts.append(alert.model_dump(mode="json"))
    write_json(ALERTS_FILE, alerts)

    return alert


def list_alerts(patient_id: str | None = None) -> list[Alert]:
    rows = read_json(ALERTS_FILE)
    if patient_id:
        rows = [row for row in rows if row["patient_id"] == patient_id]
    return [Alert(**row) for row in rows]


def start_monitoring(
    patient_id: str,
    trend: str | None = None,
    interval_seconds: int = 10,
) -> MonitoringSession:
    sessions = read_json(MONITORING_FILE)

    sessions = [row for row in sessions if row["patient_id"] != patient_id]

    session = MonitoringSession(
        patient_id=patient_id,
        active=True,
        trend=trend,
        interval_seconds=interval_seconds,
        started_at=datetime.utcnow(),
    )

    sessions.append(session.model_dump(mode="json"))
    write_json(MONITORING_FILE, sessions)

    return session


def stop_monitoring(patient_id: str) -> bool:
    sessions = read_json(MONITORING_FILE)
    original_length = len(sessions)
    sessions = [row for row in sessions if row["patient_id"] != patient_id]
    write_json(MONITORING_FILE, sessions)
    return len(sessions) != original_length


def list_monitoring_sessions() -> list[MonitoringSession]:
    return [MonitoringSession(**row) for row in read_json(MONITORING_FILE)]


def get_patient_status(patient_id: str) -> PatientLatestStatus | None:
    patient = get_patient(patient_id)
    if not patient:
        return None

    latest_vital = get_latest_vital(patient_id)
    latest_alert = get_latest_alert(patient_id)

    severity = Severity.NORMAL
    if latest_vital:
        severity = evaluate_vitals(latest_vital).severity

    return PatientLatestStatus(
        patient=patient,
        latest_vital=latest_vital,
        latest_alert=latest_alert,
        current_severity=severity,
    )


def list_all_patient_statuses() -> list[PatientLatestStatus]:
    statuses: list[PatientLatestStatus] = []

    for patient in list_patients():
        status = get_patient_status(patient.id)
        if status:
            statuses.append(status)

    return statuses


def get_patient_handover(patient_id: str) -> dict | None:
    patient = get_patient(patient_id)
    if not patient:
        return None

    recent_vitals = get_recent_vitals(patient_id, limit=8)
    alerts = list_alerts(patient_id=patient_id)

    return generate_handover_summary(
        patient=patient,
        recent_vitals=recent_vitals,
        alerts=alerts,
    )