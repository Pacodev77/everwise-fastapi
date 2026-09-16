# app/config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Everwise"
    DEBUG: bool = True
    SECRET_AUTH_KEY: str = "everwise_secure_session_key_2026_enterprise"
    DB_PATH: str = "data/everwise.db"
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings(
    GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY", "")
)
