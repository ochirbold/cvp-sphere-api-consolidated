"""Runtime settings for consolidated package layout."""
import os

class Settings:
    APP_NAME = os.getenv("APP_NAME", "CVP Optimization & Formula Engine API")
    APP_VERSION = os.getenv("APP_VERSION", "2.1.0-consolidated")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DB_HOST = os.getenv("DB_HOST", "172.169.88.80")
    DB_PORT = int(os.getenv("DB_PORT", "1521"))
    DB_SID = os.getenv("DB_SID", "DEV")

settings = Settings()
