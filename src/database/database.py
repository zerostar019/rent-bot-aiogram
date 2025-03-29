import aiomysql

# Типизация
from pymysql.err import IntegrityError
from typing import Union

# Дополнительные импорты и Redis
from config import env


class Database:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.__conn = None

    async def __connect(self) -> None:
        """
        Подключение к базе данных MySQL
        """
        self.__conn = await aiomysql.connect(
            host=env.DB_HOST.get_secret_value(),
            user=env.USER.get_secret_value(),
            password=env.PASSWORD.get_secret_value(),
            db=env.DB.get_secret_value(),
        )

    async def register_user(self, user_id: int, role: str) -> Union[int, str]:
        """
        Регистрация пользователя
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO users(user_id, role) VALUES(%s, %s)",
                        (user_id, role),
                    )
                    await conn.commit()
        except IntegrityError:
            return ("Ошибка ключа", "Данный user_id уже существует!")
        except Exception as e:
            raise e


db = Database()
