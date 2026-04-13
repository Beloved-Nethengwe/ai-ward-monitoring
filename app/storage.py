from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PATIENTS_FILE = DATA_DIR / "patients.json"
VITALS_FILE = DATA_DIR / "vitals.json"
ALERTS_FILE = DATA_DIR / "alerts.json"
MONITORING_FILE = DATA_DIR / "monitoring.json"


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for file_path in [PATIENTS_FILE, VITALS_FILE, ALERTS_FILE, MONITORING_FILE]:
        if not file_path.exists():
            file_path.write_text("[]", encoding="utf-8")


def read_json(file_path: Path) -> list[dict[str, Any]]:
    ensure_data_files()
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(file_path: Path, data: list[dict[str, Any]]) -> None:
    ensure_data_files()
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, default=str)