import aiomysql

# Типизация
from pymysql.err import IntegrityError
from typing import Union, List

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


    async def register_buy(self, user_id: int, date: str, rent_start: int, rent_end: int) -> Union[int, str]:
        """
            Обновление базы данных с покупками
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute("INSERT INTO bookings(user_id, date, rent_start, rent_end, status) "
                                      "VALUES(%s, %s, %s, %s, %s)", (user_id, date, rent_start, rent_end, 0))
                    await conn.commit()
                    return int(cur.rowcount)
        except Exception as e:
            print(e)
            raise BaseException("Error")


    async def update_booking_status(self, user_id: int, date: str, rent_start: int, rent_end: int) -> Union[int, str]:
        """
            Обновление статуса бронирования
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute("UPDATE bookings SET status = 1 WHERE user_id = %s AND date = %s AND rent_start = %s AND rent_end = %s", (user_id, date, rent_start, rent_end))
                    await conn.commit()
                    return int(cur.rowcount)
        except Exception as e:
            print(e)
            raise BaseException("Error")
        

    async def get_booking_status(self, user_id: int, date: str, rent_start: int, rent_end: int) -> Union[int, str]:
        """
            Получение статуса бронирования
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT status FROM bookings WHERE user_id = %s AND date = %s AND rent_start = %s AND rent_end = %s", (user_id, date, rent_start, rent_end))
                    result = await cur.fetchone()
                    if result is None:
                        return None
                    else:
                        return int(result[0])
        except Exception as e:
            print(e)
            raise BaseException("Error")
        
    
    async def delete_booking(self, user_id: int, date: str, rent_start: int, rent_end: int) -> Union[int, str]:
        """
            Удаление бронирования
        """
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute("DELETE FROM bookings WHERE user_id = %s AND date = %s AND rent_start = %s AND rent_end = %s", (user_id, date, rent_start, rent_end))
                    await conn.commit()
                    return int(cur.rowcount)
        except Exception as e:
            print(e)
            raise BaseException("Error")
        

    async def get_bookings_a_day(self, date: str) -> Union[List]:
        try:
            await self.__connect()
            async with self.__conn as conn:
                async with conn.cursor() as cur:
                    await cur.execute('SELECT rent_start, rent_end FROM bookings WHERE date = %s', (date,))
                    result = await cur.fetchall()
                    if result is None:
                        return None
                    else:
                        res = []
                        if len(result) > 0:
                            for k, v in result:
                                res.append({
                                    'rent_start': k,
                                    'rent_end': v
                                })
                            return res
                        return []
        except Exception as e:
            print(e)
            raise BaseException("Error")
            

db = Database()