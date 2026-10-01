from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "University Materials API"
    VERSION: str = "0.0.1"
    DEBUG: bool = False

    YANDEX_DISK_API: str = (
        "https://cloud-api.yandex.net/v1/disk/public/resources"
    )

    HTTP_TIMEOUT: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

settings = Settings()