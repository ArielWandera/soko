from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    INTERNAL_SECRET: str
    AUTH_SERVICE_URL: str = "http://auth_service:8001"

    class Config:
        env_file = ".env"


settings = Settings()
