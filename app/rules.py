from __future__ import annotations

from app.models import Severity, VitalEvaluation, VitalReading


def evaluate_vitals(vitals: VitalReading) -> VitalEvaluation:
    issues: list[str] = []

    if vitals.heart_rate > 120:
        issues.append("tachycardia")
    elif vitals.heart_rate < 50:
        issues.append("bradycardia")

    if vitals.respiratory_rate > 24:
        issues.append("tachypnea")
    elif vitals.respiratory_rate < 10:
        issues.append("bradypnea")

    if vitals.temperature > 38.5:
        issues.append("fever")
    elif vitals.temperature < 35.0:
        issues.append("hypothermia")

    if vitals.systolic_bp < 90:
        issues.append("hypotension")
    elif vitals.systolic_bp > 180:
        issues.append("severe hypertension")

    if vitals.oxygen_saturation < 92:
        issues.append("low oxygen saturation")

    if len(issues) >= 3:
        severity = Severity.HIGH
    elif len(issues) == 2:
        severity = Severity.MEDIUM
    elif len(issues) == 1:
        severity = Severity.LOW
    else:
        severity = Severity.NORMAL

    return VitalEvaluation(severity=severity, issues=issues)