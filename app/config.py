from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock").strip().lower()
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    AI_MODEL: str = os.getenv("AI_MODEL", "openai/gpt-oss-20b").strip()


settings = Settings()