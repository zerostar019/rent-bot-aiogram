from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from handlers.keyboard.start_kb import start_keyboard
from handlers.keyboard.timepicker import create_timepicker, approve_reservation, edit_timepicker
from handlers.keyboard.support_kb import approve_payment, approve_payment_timeout
from aiogram_calendar import SimpleCalendar, get_user_locale, SimpleCalendarCallback
from datetime import datetime, timedelta
from database.database import db
from bot.bot_instance import bot
from aiogram.exceptions import AiogramError
from scheduler import scheduler


# FSM
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


# Support
from handlers.support import support


class UserBuy(StatesGroup):
    date = State()
    db_date = State()
    start_hour = State()
    end_hour = State()


start = Router()
start.include_router(support)


CHAT_ID = '-4190920965'


@start.message(F.text == '/start')
async def start_bot(message: Message, fl: str | None = None):
    keyboard = await start_keyboard()
    if fl != None and fl == 'calendar_start' or fl == 'menu':
        await message.edit_text('Приветствую!', reply_markup=keyboard)
        return
    await db.register_user(user_id=message.chat.id)
    await message.answer("Приветствую!", reply_markup=keyboard)


@start.callback_query(F.data == 'menu')
async def return_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await start_bot(message=callback.message, fl='menu')


@start.callback_query(F.data == 'sign')
async def start_signing(callback: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await callback.answer()
        keyboard = SimpleCalendar(locale=await get_user_locale(callback.from_user), show_alerts=True, cancel_btn='Отмена', today_btn='Сегодня')
        await callback.message.edit_text(text="🔎 Выберите дату бронирования: ", reply_markup=await keyboard.start_calendar())
    except AiogramError as e:
        print(e)


@start.callback_query(SimpleCalendarCallback.filter())
async def pick_date(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    try:
        button_type = callback.data.split(':')[1]
        if button_type == "CANCEL":
            await start_bot(message=callback.message, fl='calendar_start')
            return
        elif button_type == 'TODAY':
            date = datetime.now().date()
            rented_times = await db.get_bookings_a_day(date=date)
            timepicker = await create_timepicker(is_today=True, rented_times=rented_times)
            if timepicker[1] == 0:
                await callback.message.edit_text(
                    text='ℹ️ К сожалению, в выбранный день нет доступного времени для бронирования!',
                    reply_markup=timepicker[0]
                )
                return
            await state.update_data(db_date=str(date))
            date = datetime.now().strftime("%d.%m.%Y")
            await state.update_data(date=date)
            await callback.message.edit_text(
                f'▶️ Вы выбрали дату: <b>{date}</b>\n\n⏳ Выберите временной диапазон:',
                reply_markup=timepicker[0],
                parse_mode="HTML"
            )
            return
        calendar = SimpleCalendar(
            locale=await get_user_locale(callback.from_user), show_alerts=True, cancel_btn='Назад', today_btn='Сегодня'
        )
        selected, date = await calendar.process_selection(callback, callback_data)
        if date:
            await state.update_data(db_date=str(date))
            rented_times = await db.get_bookings_a_day(date=date)
            date = date.strftime("%d.%m.%Y")
            date_now = datetime.now().strftime("%d.%m.%Y")
            if date.strip() == date_now.strip():
                timepicker = await create_timepicker(is_today=True)
                if timepicker[1] == 0:
                    await callback.message.edit_text(
                    text='ℹ️ К сожалению, в выбранный день нет доступного времени для бронирования!',
                    reply_markup=timepicker[0]
                )
                    return
            if date < date_now:
                await callback.answer('Невозможно забронировать в данный день!')
                await start_signing(callback, state)
                return
        if selected:
            timepicker = await create_timepicker(rented_times=rented_times)
            if timepicker[1] == 0:
                await callback.message.edit_text(
                    text='ℹ️ К сожалению, в выбранный день нет доступного времени для бронирования!',
                    reply_markup=timepicker[0]
                )
                return
            await state.update_data(date=date)
            await callback.message.edit_text(
                f'▶️ Вы выбрали дату: <b>{date}</b>\n\n⏳ Выберите временной диапазон:',
                reply_markup=timepicker[0],
                parse_mode="HTML"
            )
    except AiogramError as e:
        print(e)
        await state.clear()


@start.callback_query(F.data.startswith('hour'))
async def select_hour(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rented_times= await db.get_bookings_a_day(data['db_date'])
    if 'start_hour' in data.keys() and 'end_hour' in data.keys():
        date = data['date']
        await state.clear()
        await state.update_data(date=date)
        await state.update_data(db_date=data['db_date'])
        start_hour = int(callback.data.split('_')[1])
        await state.update_data(start_hour=start_hour)
        keyboard = await edit_timepicker(
            rented_times=rented_times,
            start_hour=start_hour,
            end_hour=None
        )
        await callback.message.edit_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=keyboard
        )

    elif 'start_hour' in data.keys():
        start_hour = data['start_hour']
        end_hour = int(callback.data.split('_')[1])
        if start_hour == end_hour:
            date = data['date']
            await state.clear()
            await state.update_data(date=date)
            await state.update_data(db_date=data['db_date'])
            keyboard = await edit_timepicker(
                rented_times=rented_times,
                start_hour=None,
                end_hour=None
            )
            await callback.message.edit_reply_markup(
                inline_message_id=callback.inline_message_id,
                reply_markup=keyboard
            )

        elif end_hour - start_hour < 2:
            await callback.answer('Минимальный срок бронирования - 2 часа!')
        else:
            await state.update_data(end_hour=end_hour)
            keyboard = await edit_timepicker(
                rented_times=rented_times,
                start_hour=start_hour,
                end_hour=end_hour
            )
            await callback.message.edit_reply_markup(
                inline_message_id=callback.inline_message_id,
                reply_markup=keyboard
            )
    else:
        start_hour = int(callback.data.split('_')[1])
        await state.update_data(start_hour=start_hour)
        keyboard = await edit_timepicker(
            rented_times=rented_times,
            start_hour=start_hour,
            end_hour=None
        )
        await callback.message.edit_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=keyboard
        )
    await callback.answer()



@start.callback_query(F.data == 'pick_date')
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await start_signing(callback, state)


@start.callback_query(F.data.startswith('pay'))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        data = await state.get_data()
        callback_data = callback.data.split('_')
        payment_sum = callback_data[1]
        start_hour = data['start_hour']
        end_hour = data['end_hour']
        text = f'ℹ️ <b>Информация о бронировании:</b>\n\n📆 Дата бронирования: <b>{data["date"]}</b>\n\n🕔 Время бронирования:\n\n'
        text += f' <b>{start_hour}.00 - {end_hour}.00</b>\n\n'
        text += f'Общая стоимость: <i><b>{payment_sum}</b></i> руб.\n\n'
        text += '➡️ Для продолжения, подтвердите бронирование!'
        keyboard = await approve_reservation()  
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    except AiogramError as e:
        print(e)
        await state.clear()


async def send_deny_message(message: Message, chat_id: int, date: str, rent_start: int, rent_end: int):
    try:
        keyboard = await approve_payment_timeout(user_id=chat_id)
        booking_status = await db.get_booking_status(user_id=chat_id, date=date, rent_start=rent_start, rent_end=rent_end)
        if booking_status == 0:
            text = '❗️ Истекло время оплаты!\n\n'
            text += message.text
            await message.edit_text(text=text, reply_markup=keyboard)
            await bot.send_message(chat_id=chat_id, text='ℹ️ Истекло время оплаты!\n\nК сожалению, бронирование отменено!')
            await db.delete_booking(user_id=chat_id, date=date, rent_start=rent_start, rent_end=rent_end)
        else:
            pass
    except Exception as e:
        print(e)
        pass


@start.callback_query(F.data == 'approve')
async def process_approve(callback: CallbackQuery, state: FSMContext):
    try:
        # Обработка сообщений пользователя и отправка брони в базу данных
        # Получение данных о брони
        data = await state.get_data()
        date = data['date'].split('.')
        date = f'{date[2]}-{date[1]}-{date[0]}'
        rent_start = data['start_hour']
        rent_end = data['end_hour']

        user_id = callback.message.chat.id

        # Отправка сообщения пользователю
        keyboard = await approve_payment(user_id=user_id)
        await callback.answer()
        await callback.message.delete_reply_markup(inline_message_id=callback.inline_message_id)
        await callback.message.answer('👌 Успешное бронирование!\n\n💸 Пожалуйста, внесите оплату в течение 15 минут по указанным реквизитам и ожидайте ответа Администратора!')
        msg = await bot.send_message(chat_id=CHAT_ID, reply_markup=keyboard, text=callback.message.text.replace('➡️ Для продолжения, подтвердите бронирование!', f'#{user_id}_{date}_{rent_start}_{rent_end}'))
        
        # Добавление в базу данных брони пользователя
        run_date = datetime.now() + timedelta(seconds=10)
        job_args = (msg, user_id, date, rent_start, rent_end,)
        scheduler.add_job(send_deny_message, 'date', run_date=run_date, args=job_args)
        await db.register_buy(user_id=int(user_id), date=date, rent_start=rent_start, rent_end=rent_end)
        await state.clear()
    except AiogramError as e:
        print(e)
        await state.clear()