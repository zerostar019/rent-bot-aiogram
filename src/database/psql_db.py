import asyncpg
from asyncpg import Range
from datetime import datetime, timedelta

# дополнительные импорты
from src.config import env
from typing import Union
from contextlib import asynccontextmanager
from typing import Optional, List, Dict


class Database:
    def __init__(self):
        self.pool = None  # Пул подключений

    async def connect(self):
        """Создает пул подключений при запуске приложения"""
        try:
            self.pool = await asyncpg.create_pool(
                user=env.DB_USER.get_secret_value(),
                password=env.DB_PASSWORD.get_secret_value(),
                database=env.DB_NAME.get_secret_value(),
                host=env.DB_HOST.get_secret_value(),
            )
            return True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return False

    async def close(self):
        """Закрывает пул подключений"""
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def acquire_connection(self):
        """Контекстный менеджер для безопасного получения подключения из пула"""
        async with self.pool.acquire() as conn:
            yield conn

    # async def get_users_chat(self) -> Optional[List[Dict]]:
    #     """Получить пользователей с количеством непрочитанных сообщений"""
    #     try:
    #         async with self.acquire_connection() as conn:
    #             async with conn.transaction():
    #                 data = await conn.fetch("""
    #                     SELECT u.user_id, COUNT(c.id) AS unread_count
    #                     FROM users u
    #                     LEFT JOIN chat c ON u.user_id = c.user_id AND c.read_at IS NULL
    #                     AND c.user_id != 111 WHERE u.user_id != 111
    #                     GROUP BY u.user_id;
    #                 """)
    #                 return [dict(record) for record in data]
    #     except Exception as e:
    #         print(f"Ошибка при получении пользователей: {e}")
    #         return None


    async def get_users_chat(self) -> Optional[List[Dict]]:
        """Получить пользователей с непрочитанными сообщениями, у которых есть хотя бы одно сообщение"""
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    data = await conn.fetch("""
                        SELECT 
                            u.user_id,
                            SUM(CASE WHEN c.read_at IS NULL THEN 1 ELSE 0 END) AS unread_count
                        FROM users u
                        INNER JOIN chat c ON u.user_id = c.user_id AND c.user_id != 111
                        GROUP BY u.user_id
                        ORDER BY MAX(c.created_at) DESC;
                    """)
                    return [dict(record) for record in data]
        except Exception as e:
            print(f"Ошибка при получении пользователей: {e}")
            return None

    async def get_chat_by_user_id(self, user_id: int) -> Optional[List[Dict]]:
        """Получить чат с пользователем"""
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    data = await conn.fetch(
                        """
                        SELECT 
                            chat.*,
                            rental.approved AS approved
                        FROM chat
                        LEFT JOIN rental ON chat.booking_id = rental.id
                        WHERE chat.chat_id = $1
                        ORDER BY created_at ASC;
                        """,
                        user_id,
                    )
                    messages = [dict(record) for record in data]
                    for msg in messages:
                        if isinstance(msg["created_at"], datetime):
                            msg["created_at"] = msg["created_at"].isoformat()
                        if msg["read_at"] and isinstance(msg["read_at"], datetime):
                            msg["read_at"] = msg["read_at"].isoformat()
                    return messages
        except Exception as e:
            print(f"Ошибка при получении чата: {e}")
            return None

    async def update_read_at(self, chat_id: int) -> bool:
        """Обновить статус прочтения сообщений"""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute(
                    """
                    UPDATE chat 
                    SET read_at = NOW() 
                    WHERE user_id = $1;
                """,
                    chat_id,
                )
                return True
        except Exception as e:
            print(f"Ошибка при обновлении read_at: {e}")
            return None

    async def new_rental(
        self,
        user_id: int,
        rent_type: str,
        time_interval: list,
        amount: str,
        from_panel: bool = False,
    ) -> Union[None, bool, int]:
        """
        Новая бронь

        :param rent_type:
        :param time_interval:
        :param user_id:
        :return:
        """
        try:
            time_range = Range(
                datetime(
                    time_interval[0][0],
                    time_interval[0][1],
                    time_interval[0][2],
                    time_interval[0][3],
                    time_interval[0][4],
                ),
                datetime(
                    time_interval[1][0],
                    time_interval[1][1],
                    time_interval[1][2],
                    time_interval[1][3],
                    time_interval[1][4],
                ),
                upper_inc=True,
                lower_inc=False,
            )

            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    result = await conn.fetchval(
                        """
                        INSERT INTO Rental (id_user, created_at, rent_type, time_interval, amount, approved)
                        VALUES ($1, NOW(), $2, $3::TSRANGE, $4, $5) RETURNING id;
                        """,
                        user_id,
                        rent_type,
                        time_range,
                        amount,
                        from_panel,
                    )
                    if result is not None:
                        return result
                    return None
        except Exception as e:
            print(f"Error creating rental: {e}")
            return None

    async def update_rental(
        self,
        id_rental: int,
        user_id: int,
        rent_type: str,
        time_interval: list,
        amount: int,
        approved: bool,
    ) -> Union[None, int]:
        """
        Обновление существующей брони

        :param amount: Сумма бронирования
        :param id_rental: ID брони для обновления
        :param rent_type: Тип бронирования
        :param time_interval: Временной интервал
        :param user_id: ID пользователя
        :return
        """
        try:
            time_range = Range(
                datetime(
                    time_interval[0][0],
                    time_interval[0][1],
                    time_interval[0][2],
                    time_interval[0][3],
                    time_interval[0][4],
                ),
                datetime(
                    time_interval[1][0],
                    time_interval[1][1],
                    time_interval[1][2],
                    time_interval[1][3],
                    time_interval[1][4],
                ),
                upper_inc=True,
                lower_inc=False,
            )

            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    result = await conn.fetchval(
                        """
                            UPDATE Rental 
                        SET id_user = $1, 
                            rent_type = $2, 
                            time_interval = $3::TSRANGE, 
                            amount = $4,
                            approved = $5
                        WHERE id = $6
                        RETURNING id;
                            """,
                        user_id,
                        rent_type,
                        time_range,
                        amount,
                        approved,
                        id_rental,
                    )
                    if result is not None:
                        return result
                    return None
        except Exception as e:
            print(f"Error updating rental: {e}")
            return None

    async def get_booking_data_by_id(self, booking_id: int) -> Union[dict, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    booking_data = await conn.fetchrow(
                        """
                        SELECT * FROM Rental WHERE id = $1
                        """,
                        booking_id,
                    )
                    if booking_data is not None:
                        data = dict(booking_data)
                        for key, value in data.items():
                            if isinstance(value, datetime):
                                data[key] = value.isoformat()
                            elif isinstance(value, asyncpg.Range):
                                start = value.lower.isoformat() if value.lower else None
                                end = value.upper.isoformat() if value.upper else None
                                data[key] = {"start": start, "end": end}
                        return data
                    return None
        except Exception as e:
            print(f"Error getting rent data: {e}")
            return None

    async def delete_booking_by_id(self, booking_id: int) -> Union[bool, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    deleted_row = await conn.execute(
                        """
                            DELETE FROM Rental 
                            WHERE id = $1
                            RETURNING id
                            """,
                        booking_id,
                    )
                    await conn.execute(
                        """
                        DELETE FROM chat
                        WHERE booking_id = $1
                        RETURNING id
                        """,
                        booking_id,
                    )
                    if deleted_row:
                        return True
                    else:
                        return False
        except Exception as e:
            print(f"Error deleting rental: {e}")
            return None

    async def get_booked_days(self, date_array: list) -> list:
        """Получить список занятых дат на месяц вперед от заданной даты

        :param date_array:
        :return:
        """
        try:
            # Преобразуем входной массив в datetime
            year, month, day, hour, minute = date_array
            start_dt = datetime(year, month, day, hour, minute)
            end_dt = start_dt + timedelta(days=60)  # 2 месяца вперед

            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    # Запрос для поиска всех пересечений с нашим периодом
                    records = await conn.fetch(
                        """
                            SELECT DISTINCT
                                date(generate_series(
                                    GREATEST(lower(time_interval), $1::timestamp),
                                    LEAST(upper(time_interval) - interval '1 second', $2::timestamp),
                                    interval '1 day'
                                )) AS booked_date
                            FROM Rental
                            WHERE rent_type = 'daily'
                            AND time_interval && tsrange($1::timestamp, $2::timestamp)
                            ORDER BY booked_date;
                        """,
                        start_dt,
                        end_dt,
                    )

                    # Форматируем даты в нужный строковый формат
                    return [
                        record["booked_date"].strftime("%d.%m.%Y") for record in records
                    ]
        except Exception as e:
            print(f"Ошибка при получении занятых дней: {e}")
            return []

    async def register_user(self, telegram_id: int) -> Union[None, bool]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    await conn.fetchval(
                        """
                            INSERT INTO users (user_id)
                            VALUES ($1);
                            """,
                        telegram_id,
                    )
                    return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return None

    async def check_user_registered(self, telegram_id: int) -> Union[bool, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    result = await conn.fetchval(
                        """
                        SELECT * FROM users
                        WHERE user_id=$1;
                        """,
                        telegram_id,
                    )
                    if result is not None:
                        return True
                    return None
        except Exception as e:
            print(f"Error checking user: {e}")
            return None

    async def save_file_from_bot(
        self,
        file_name: str,
        file_path: str,
        user_id: int,
        message_text: str,
        chat_id: int,
        booking_id: int = None,
    ) -> Union[bool, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    file_id = await conn.fetchval(
                        """
                        INSERT INTO files (file_path, file_name)
                        VALUES ($1, $2) RETURNING id;
                        """,
                        file_path,
                        file_name,
                    )
                    message = await conn.fetchrow(
                        """
                        INSERT INTO chat (message, user_id, file_id, created_at, chat_id, booking_id)
                        VALUES($1, $2, $3, NOW(), $4, $5) RETURNING *;
                        """,
                        message_text,
                        user_id,
                        file_id,
                        chat_id,
                        booking_id,
                    )
                    message = dict(message)
                    message["created_at"] = message["created_at"].isoformat()
                    if message["read_at"] and isinstance(message["read_at"], datetime):
                        message["read_at"] = message["read_at"].isoformat()
                    return dict(message)
        except Exception as e:
            print(f"Error checking user: {e}")
            return None

    async def save_message_from_bot(
        self, message_text: str, user_id: int
    ) -> Union[bool, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    message = await conn.fetchrow(
                        """
                        INSERT INTO chat (message, user_id, created_at, chat_id)
                        VALUES ($1, $2, NOW(), $3) RETURNING *;
                        """,
                        message_text,
                        user_id,
                        user_id,
                    )
                    message = dict(message)
                    message["created_at"] = message["created_at"].isoformat()
                    if message["read_at"] and isinstance(message["read_at"], datetime):
                        message["read_at"] = message["read_at"].isoformat()
                    return dict(message)
        except Exception as e:
            print(f"Error saving message from bot: {e}")
            return None

    async def save_message_from_panel(
        self, message_text: str, chat_id: int
    ) -> Union[bool, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    message = await conn.fetchrow(
                        """
                        INSERT INTO chat (message, user_id, created_at, chat_id)
                        VALUES ($1, $2, NOW(), $3) RETURNING *;
                        """,
                        message_text,
                        111,
                        chat_id,
                    )
                    message = dict(message)
                    message["created_at"] = message["created_at"].isoformat()
                    if message["read_at"] and isinstance(message["read_at"], datetime):
                        message["read_at"] = message["read_at"].isoformat()
                    return dict(message)
        except Exception as e:
            print(f"Error saving message from panel: {e}")
            return None

    async def get_file_path(self, file_id: int) -> Union[str, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    file_path = await conn.fetchrow(
                        """
                        SELECT * FROM files WHERE id = $1;
                        """,
                        file_id,
                    )
                    return dict(file_path)
        except Exception as e:
            print(f"Error fetching file_path: {e}")
            return None

    async def get_admins(self) -> Union[str, None]:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    admins = await conn.fetch(
                        """
                        SELECT * FROM admins;
                        """,
                    )
                    return list(dict(admin)["user_id"] for admin in admins)
        except Exception as e:
            print(f"Error fetching file_path: {e}")
            return None

    def serialize_record(self, record):
        def convert_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, asyncpg.Range):  # Для tsrange
                start = value.lower.isoformat() if value.lower else ""
                end = value.upper.isoformat() if value.upper else ""
                return f"[{start}, {end})"
            return value  # Остальные типы остаются как есть

        # Преобразуем record в словарь и добавляем 'key' = 'id'
        data = dict(record)
        data["key"] = data["id"]  # Добавляем несуществующий столбец 'key'

        # Применяем конвертацию только к существующим полям
        return {key: convert_value(value) for key, value in data.items()}

    async def get_bookings(
        self, select_base: str, limit_offset: str, count_query: str, params: list
    ) -> any:
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    records = await conn.fetch(select_base + limit_offset, *params)

                    # Преобразуем все datetime и tsrange в строки, добавляем 'key'
                    processed_records = [
                        self.serialize_record(record) for record in records
                    ]

                    total = await conn.fetchval(count_query, *params[:-2])
                    return {
                        "data": processed_records,
                        "total": total,
                    }
        except Exception as e:
            print(f"Error fetching bookings: {e}")
            return None

    async def update_rental_status(
        self,
        id_rental: int,
        approved: bool,
    ) -> Union[None, int]:
        """
        Обновление существующей брони

        :param amount: Сумма бронирования
        :param id_rental: ID брони для обновления
        :param approved: Статус брони
        :return
        """
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
                    result = await conn.fetchrow(
                        """
                        UPDATE Rental 
                        SET approved = $1
                        WHERE id = $2
                        RETURNING *;
                            """,
                        approved,
                        id_rental,
                    )
                    if result is not None:
                        return dict(result)
                    return None
        except Exception as e:
            print(f"Error updating rental status: {e}")
            return None

    async def get_blocked_days(
        self, start_date_array: list[int], check_days_ahead: int = 30
    ) -> list[str]:
        """
        Возвращает все даты недоступные для выбора окончания бронирования, после выбора даты заезда.
        Example:
        db.get_blocked_days([2025, 5, 30, 14, 00])
        :param start_date_array: [year, month, day, hour, minute]
        :param check_days_ahead:
        :return:
        """
        year, month, day, hour, minute = start_date_array
        checkin_base = datetime(year, month, day, 14, 0)

        first_booking_day = None

        async with self.acquire_connection() as conn:
            for i in range(1, check_days_ahead + 1):
                checkout_day = checkin_base + timedelta(days=i)
                checkout_time = datetime(
                    checkout_day.year, checkout_day.month, checkout_day.day, 13, 0
                )
                rental_start = checkin_base
                rental_end = checkout_time

                query = """
                        SELECT EXISTS (
                            SELECT 1 FROM Rental
                            WHERE time_interval && TSRANGE($1, $2)
                        );
                    """

                is_booked: bool = await conn.fetchval(query, rental_start, rental_end)
                if is_booked:
                    first_booking_day = checkout_day
                    break  # Останавливаемся на первом пересечении

        if not first_booking_day:
            return []  # Нет пересечений — ничего не блокируем

        # Теперь собираем все дни с first_booking_day до конца месяца
        end_of_month = (first_booking_day.replace(day=28) + timedelta(days=4)).replace(
            day=1
        ) - timedelta(days=1)
        current_day = first_booking_day
        blocked_days = []

        while current_day <= end_of_month:
            blocked_days.append(current_day.strftime("%d.%m.%Y"))
            current_day += timedelta(days=1)

        return blocked_days


db = Database()
