from __future__ import annotations

import json
from statistics import mean
from typing import Any

import google.generativeai as genai

from app.config import settings
from app.models import Alert, Patient, VitalReading


def calculate_delta(old: float | int, new: float | int) -> float:
    return round(float(new) - float(old), 2)


def summarize_vital_trend(vitals: list[VitalReading]) -> dict[str, Any]:
    if not vitals:
        return {
            "count": 0,
            "trend_text": "No recent vital signs available.",
            "metrics": {},
        }

    ordered = sorted(
        [v for v in vitals if v.timestamp is not None],
        key=lambda x: x.timestamp,
    )

    if not ordered:
        return {
            "count": 0,
            "trend_text": "No timestamped vital signs available.",
            "metrics": {},
        }

    latest = ordered[-1]
    first = ordered[0]

    metrics = {
        "heart_rate": {
            "latest": latest.heart_rate,
            "change": calculate_delta(first.heart_rate, latest.heart_rate),
            "average": round(mean(v.heart_rate for v in ordered), 1),
        },
        "respiratory_rate": {
            "latest": latest.respiratory_rate,
            "change": calculate_delta(first.respiratory_rate, latest.respiratory_rate),
            "average": round(mean(v.respiratory_rate for v in ordered), 1),
        },
        "temperature": {
            "latest": latest.temperature,
            "change": calculate_delta(first.temperature, latest.temperature),
            "average": round(mean(v.temperature for v in ordered), 1),
        },
        "systolic_bp": {
            "latest": latest.systolic_bp,
            "change": calculate_delta(first.systolic_bp, latest.systolic_bp),
            "average": round(mean(v.systolic_bp for v in ordered), 1),
        },
        "oxygen_saturation": {
            "latest": latest.oxygen_saturation,
            "change": calculate_delta(first.oxygen_saturation, latest.oxygen_saturation),
            "average": round(mean(v.oxygen_saturation for v in ordered), 1),
        },
    }

    trend_lines = [
        f"Heart rate latest {metrics['heart_rate']['latest']} (change {metrics['heart_rate']['change']})",
        f"Respiratory rate latest {metrics['respiratory_rate']['latest']} (change {metrics['respiratory_rate']['change']})",
        f"Temperature latest {metrics['temperature']['latest']} (change {metrics['temperature']['change']})",
        f"Systolic BP latest {metrics['systolic_bp']['latest']} (change {metrics['systolic_bp']['change']})",
        f"SpO2 latest {metrics['oxygen_saturation']['latest']} (change {metrics['oxygen_saturation']['change']})",
    ]

    return {
        "count": len(ordered),
        "trend_text": "; ".join(trend_lines),
        "metrics": metrics,
    }


def build_alert_prompt(
    patient: Patient,
    latest_vital: VitalReading,
    recent_vitals: list[VitalReading],
    issues: list[str],
) -> str:
    trend = summarize_vital_trend(recent_vitals)

    return f"""
You are assisting with ward deterioration summaries for a non-ICU patient.

Rules:
- Write a short, clinically cautious summary
- Mention why the patient was flagged
- Mention important recent trend changes
- Suggest escalation wording
- Do not diagnose definitively
- Do not prescribe medication
- Do not give treatment instructions
- Keep the response concise and professional

Patient context:
- Name: {patient.name} {patient.surname}
- Ward: {patient.ward}
- Bed: {patient.bed}
- Assigned nurse: {patient.assigned_nurse}
- Admission reason: {patient.admission_reason}
- Surgeries: {", ".join(patient.surgeries) if patient.surgeries else "none recorded"}
- Notes: {patient.notes or "none"}

Latest vital signs:
- Heart rate: {latest_vital.heart_rate}
- Respiratory rate: {latest_vital.respiratory_rate}
- Temperature: {latest_vital.temperature}
- Blood pressure: {latest_vital.systolic_bp}/{latest_vital.diastolic_bp}
- Oxygen saturation: {latest_vital.oxygen_saturation}

Detected issues:
- {", ".join(issues) if issues else "none"}

Recent trend summary:
- {trend["trend_text"]}

Return only valid JSON in this exact shape:
{{
  "risk_summary": "string",
  "concerns_to_consider": ["string", "string"],
  "escalation": "string"
}}
""".strip()


def generate_mock_ai_summary(
    patient: Patient,
    latest_vital: VitalReading,
    recent_vitals: list[VitalReading],
    issues: list[str],
) -> dict[str, Any]:
    trend = summarize_vital_trend(recent_vitals)
    metrics = trend["metrics"]

    concern_candidates: list[str] = []

    if "fever" in issues and "tachycardia" in issues:
        concern_candidates.append("possible infection-related deterioration")
    if "low oxygen saturation" in issues or "tachypnea" in issues:
        concern_candidates.append("possible respiratory compromise")
    if "hypotension" in issues and "tachycardia" in issues:
        concern_candidates.append("possible circulatory instability")
    if not concern_candidates:
        concern_candidates.append("general clinical deterioration")

    risk_summary = (
        f"{patient.name} {patient.surname} has been flagged for abnormal ward vital signs. "
        f"Current concerns include {', '.join(issues)}. "
        f"Recent trends show HR change {metrics.get('heart_rate', {}).get('change', 0)}, "
        f"RR change {metrics.get('respiratory_rate', {}).get('change', 0)}, "
        f"Temp change {metrics.get('temperature', {}).get('change', 0)}, "
        f"SBP change {metrics.get('systolic_bp', {}).get('change', 0)}, "
        f"and SpO2 change {metrics.get('oxygen_saturation', {}).get('change', 0)}."
    )

    if len(issues) >= 3:
        escalation = "Urgent clinical review should be considered."
    elif len(issues) == 2:
        escalation = "Prompt clinician review and repeat observations should be considered."
    else:
        escalation = "Repeat observations and ward review should be considered."

    return {
        "risk_summary": risk_summary,
        "concerns_to_consider": concern_candidates,
        "escalation": escalation,
    }


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        return json.loads(candidate)

    raise ValueError("No valid JSON object found in model response")


def call_external_ai(prompt: str) -> dict[str, Any]:
    print("Entered call_external_ai")

    print("AI_PROVIDER =", settings.AI_PROVIDER)
    print("AI_MODEL =", settings.AI_MODEL)
    print("Has API key =", bool(settings.AI_API_KEY))

    if settings.AI_PROVIDER != "gemini_legacy":
        raise RuntimeError(f"External AI provider not enabled. Got: {settings.AI_PROVIDER}")

    if not settings.AI_API_KEY:
        raise RuntimeError("Missing Gemini API key")

    genai.configure(api_key=settings.AI_API_KEY)
    model = genai.GenerativeModel(settings.AI_MODEL)

    print("Sending prompt to Gemini...")
    response = model.generate_content(prompt)

    print("Raw response object:", response)

    text = getattr(response, "text", None)
    print("AI response text:", text)

    if not text:
        raise RuntimeError("Gemini returned an empty response")

    data = extract_json_object(text)
    print("Parsed JSON:", data)

    if not isinstance(data, dict):
        raise RuntimeError("Gemini response was not a JSON object")

    return {
        "risk_summary": data.get("risk_summary", ""),
        "concerns_to_consider": data.get("concerns_to_consider", []),
        "escalation": data.get("escalation", ""),
    }

def get_ai_alert_summary(
    patient: Patient,
    latest_vital: VitalReading,
    recent_vitals: list[VitalReading],
    issues: list[str],
) -> dict[str, Any]:
    prompt = build_alert_prompt(patient, latest_vital, recent_vitals, issues)

    try:
        return call_external_ai(prompt)
    except Exception:
        return generate_mock_ai_summary(
            patient=patient,
            latest_vital=latest_vital,
            recent_vitals=recent_vitals,
            issues=issues,
        )


def format_alert_summary_text(summary_data: dict[str, Any]) -> str:
    concerns = summary_data.get("concerns_to_consider", [])
    concerns_text = ", ".join(concerns) if concerns else "No specific concerns listed"

    return (
        f"{summary_data.get('risk_summary', '')} "
        f"Concerns to consider: {concerns_text}. "
        f"{summary_data.get('escalation', '')}"
    ).strip()


def generate_handover_summary(
    patient: Patient,
    recent_vitals: list[VitalReading],
    alerts: list[Alert],
) -> dict[str, Any]:
    trend = summarize_vital_trend(recent_vitals)

    latest_alert = None
    timestamped_alerts = [a for a in alerts if a.timestamp is not None]
    if timestamped_alerts:
        latest_alert = sorted(timestamped_alerts, key=lambda x: x.timestamp)[-1]

    return {
        "patient": f"{patient.name} {patient.surname}",
        "location": f"{patient.ward} bed {patient.bed}",
        "admission_reason": patient.admission_reason,
        "surgeries": patient.surgeries,
        "notes": patient.notes,
        "recent_vitals_count": trend["count"],
        "trend_summary": trend["trend_text"],
        "latest_alert_severity": latest_alert.severity if latest_alert else None,
        "latest_alert_summary": latest_alert.summary if latest_alert else None,
    }