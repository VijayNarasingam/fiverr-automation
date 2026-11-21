from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Fiverr credentials
    FIVERR_EMAIL: str
    FIVERR_PASSWORD: str
    FIVERR_2FA_SECRET: str = ""

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_JSON: str
    GOOGLE_SHEET_ID: str

    # NVIDIA (Nemotron 3.5 Super VL 120B A12B)
    NVIDIA_BASE_URL: str
    NVIDIA_API_KEY: str
    NVIDIA_MODEL: str

    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # Notifications
    DISCORD_WEBHOOK_URL: str = ""
    SLACK_WEBHOOK_URL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Proxies
    PROXY_API_URLS: str = ""

    # Rate limits
    RATE_LIMIT_PER_HOUR: int = 3
    MAX_GIGS_PER_RUN: int = 2

    # Security
    SECRET_KEY: str = "dev-secret-change-me"

    class Config:
        env_file = ".env"


settings = Settings()