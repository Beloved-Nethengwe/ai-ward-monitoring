from __future__ import annotations

import random
from typing import Optional

from app.models import VitalReading


def clamp(value: int | float, minimum: int | float, maximum: int | float) -> int | float:
    return max(minimum, min(value, maximum))


def random_walk(value: int | float, step_min: int | float, step_max: int | float) -> int | float:
    return value + random.uniform(step_min, step_max)


def create_baseline_vitals(patient_id: str) -> VitalReading:
    return VitalReading(
        patient_id=patient_id,
        timestamp=None,  # set later by caller
        heart_rate=random.randint(72, 95),
        respiratory_rate=random.randint(14, 19),
        temperature=round(random.uniform(36.4, 37.2), 1),
        systolic_bp=random.randint(112, 128),
        diastolic_bp=random.randint(72, 84),
        oxygen_saturation=random.randint(97, 100),
    )


def apply_normal_variation(
    heart_rate: float,
    respiratory_rate: float,
    temperature: float,
    systolic_bp: float,
    diastolic_bp: float,
    oxygen_saturation: float,
) -> tuple[float, float, float, float, float, float]:
    heart_rate = random_walk(heart_rate, -3, 3)
    respiratory_rate = random_walk(respiratory_rate, -1, 1)
    temperature = random_walk(temperature, -0.1, 0.1)
    systolic_bp = random_walk(systolic_bp, -3, 3)
    diastolic_bp = random_walk(diastolic_bp, -2, 2)
    oxygen_saturation = random_walk(oxygen_saturation, -1, 1)

    return (
        heart_rate,
        respiratory_rate,
        temperature,
        systolic_bp,
        diastolic_bp,
        oxygen_saturation,
    )


def apply_trend(
    trend: Optional[str],
    heart_rate: float,
    respiratory_rate: float,
    temperature: float,
    systolic_bp: float,
    diastolic_bp: float,
    oxygen_saturation: float,
) -> tuple[float, float, float, float, float, float]:
    if trend == "infection":
        heart_rate += random.uniform(2, 6)
        respiratory_rate += random.uniform(1, 3)
        temperature += random.uniform(0.1, 0.3)
        systolic_bp -= random.uniform(1, 4)
        oxygen_saturation -= random.uniform(0, 1.5)

    elif trend == "respiratory":
        respiratory_rate += random.uniform(2, 4)
        oxygen_saturation -= random.uniform(1, 3)
        heart_rate += random.uniform(1, 4)
        temperature += random.uniform(-0.1, 0.2)

    elif trend == "bleeding":
        heart_rate += random.uniform(3, 7)
        systolic_bp -= random.uniform(3, 6)
        diastolic_bp -= random.uniform(1, 4)
        respiratory_rate += random.uniform(1, 3)
        oxygen_saturation += random.uniform(-1, 0.5)

    elif trend == "recovery":
        heart_rate -= random.uniform(1, 4)
        respiratory_rate -= random.uniform(0.5, 2)
        temperature -= random.uniform(0.0, 0.2)
        systolic_bp += random.uniform(1, 3)
        diastolic_bp += random.uniform(0.5, 2)
        oxygen_saturation += random.uniform(0, 1.5)

    return (
        heart_rate,
        respiratory_rate,
        temperature,
        systolic_bp,
        diastolic_bp,
        oxygen_saturation,
    )


def build_next_vitals(patient_id: str, previous: VitalReading | None, trend: Optional[str]) -> VitalReading:
    if previous is None:
        baseline = create_baseline_vitals(patient_id)
        heart_rate = baseline.heart_rate
        respiratory_rate = baseline.respiratory_rate
        temperature = baseline.temperature
        systolic_bp = baseline.systolic_bp
        diastolic_bp = baseline.diastolic_bp
        oxygen_saturation = baseline.oxygen_saturation
    else:
        heart_rate = previous.heart_rate
        respiratory_rate = previous.respiratory_rate
        temperature = previous.temperature
        systolic_bp = previous.systolic_bp
        diastolic_bp = previous.diastolic_bp
        oxygen_saturation = previous.oxygen_saturation

    (
        heart_rate,
        respiratory_rate,
        temperature,
        systolic_bp,
        diastolic_bp,
        oxygen_saturation,
    ) = apply_normal_variation(
        heart_rate,
        respiratory_rate,
        temperature,
        systolic_bp,
        diastolic_bp,
        oxygen_saturation,
    )

    (
        heart_rate,
        respiratory_rate,
        temperature,
        systolic_bp,
        diastolic_bp,
        oxygen_saturation,
    ) = apply_trend(
        trend,
        heart_rate,
        respiratory_rate,
        temperature,
        systolic_bp,
        diastolic_bp,
        oxygen_saturation,
    )

    heart_rate = int(clamp(round(heart_rate), 35, 180))
    respiratory_rate = int(clamp(round(respiratory_rate), 6, 40))
    temperature = round(float(clamp(temperature, 33.0, 41.5)), 1)
    systolic_bp = int(clamp(round(systolic_bp), 60, 220))
    diastolic_bp = int(clamp(round(diastolic_bp), 35, 130))
    oxygen_saturation = int(clamp(round(oxygen_saturation), 75, 100))

    return VitalReading(
        patient_id=patient_id,
        timestamp=None,  # set later by caller
        heart_rate=heart_rate,
        respiratory_rate=respiratory_rate,
        temperature=temperature,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        oxygen_saturation=oxygen_saturation,
    )