from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost/auth/google/callback"
<<<<<<< HEAD
    FRONTEND_URL: str
    USER_SERVICE_URL: str
=======
    FRONTEND_URL: str = "http://localhost:3000"
>>>>>>> 3500cb5 (feat(auth): lower bcrypt rounds, make OAuth config optional, restore refresh endpoint)


    class Config:
        env_file = ".env"





settings = Settings()
