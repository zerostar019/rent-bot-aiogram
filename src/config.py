from pydantic_settings import BaseSettings
from pydantic import SecretStr
import pathlib


PATH_TO_ENV = str(pathlib.Path(__file__).resolve().parent.parent) + '/.env'


class Environment(BaseSettings):
    HOST: SecretStr
    TOKEN: SecretStr
    PORT: SecretStr
    DB_HOST: SecretStr
    USER: SecretStr
    PASSWORD: SecretStr
    DB: SecretStr


    class Config:
        env_file = PATH_TO_ENV
        env_file_encoding = 'utf-8'


env = Environment()