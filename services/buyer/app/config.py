from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    SECRET_KEY: str = "supersecretkey_change_in_prod"
    ALGORITHM: str = "HS256"
    # Internal service URLs — using Docker service names as hostnames
    PRODUCE_SERVICE_URL: str = "http://produce_service:8004"

    class Config:
        env_file = ".env"


settings = Settings()
