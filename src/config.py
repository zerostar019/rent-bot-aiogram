from pydantic_settings import BaseSettings
from pydantic import SecretStr
import pathlib


PATH_TO_ENV = str(pathlib.Path(__file__).resolve().parent.parent) + "/.env"


class Environment(BaseSettings):
    HOST: SecretStr
    TOKEN: SecretStr
    PORT: SecretStr
    DB_HOST: SecretStr
    DB_USER: SecretStr
    DB_PASSWORD: SecretStr
    DB_NAME: SecretStr
    PASSWORD: SecretStr
    DB: SecretStr
    PROXY: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr | None = None

    class Config:
        extra = "ignore"
        env_file = PATH_TO_ENV
        env_file_encoding = "utf-8"


env = Environment()
