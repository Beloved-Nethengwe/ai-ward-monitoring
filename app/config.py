from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock").strip().lower()
    AI_API_KEY: str = os.getenv("AI_API_KEY", "").strip()
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-1.5-flash").strip()


settings = Settings()