from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # DB
    database_url: str = "postgresql+psycopg2://planpilot:planpilot@localhost:5432/planpilot"

    # App
    app_name: str = "PlanPilot"


settings = Settings()
