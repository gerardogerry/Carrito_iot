from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root2004"
    DB_NAME: str = "vehiculo_iot"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()