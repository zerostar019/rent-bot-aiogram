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
            db=env.DB.get_secret_value()
        )

    async def register_user(self, user_id: int, buys: int = 0) -> Union[int, str]:
        """
            Регистрация пользователя
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute("INSERT INTO users_info(id, buys_count) "
                                      "VALUES(%s, %s)", (user_id, buys))
                    await conn.commit()
                    return int(cur.rowcount)
        except IntegrityError:
            return ("Ошибка ключа", "Данный user_id уже существует!")
        except Exception as e:
            print(e)
            raise BaseException("Error")


    async def register_buy(self, user_id: int, date: str, time: str) -> Union[int, str]:
        """
            Обновление базы данных с покупками
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute("INSERT INTO buys(user_id, date, time, status) "
                                      "VALUES(%s, %s, %s, %s)", (user_id, date, time, 0))
                    await conn.commit()
                    return int(cur.rowcount)
        except Exception as e:
            print(e)
            raise BaseException("Error")


    async def update_booking_status(self, user_id: int, date: str, time: str) -> Union[int, str]:
        """
            Обновление статуса бронирования
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute("UPDATE buys SET status = 1 WHERE user_id = %s AND date = %s AND time = %s", (user_id, date, time))
                    await conn.commit()
                    return int(cur.rowcount)
        except Exception as e:
            print(e)
            raise BaseException("Error")

db = Database()