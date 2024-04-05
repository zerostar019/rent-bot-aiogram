from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from handlers.keyboard.start_kb import start_keyboard
from handlers.keyboard.timepicker import create_timepicker, edit_timepicker, approve_reservation
from handlers.keyboard.support_kb import approve_payment
from aiogram_calendar import SimpleCalendar, get_user_locale, SimpleCalendarCallback
from datetime import datetime
from database.database import db
from bot.bot_instance import bot
from aiogram.exceptions import AiogramError

# FSM
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


# Support
from handlers.support import support


class UserBuy(StatesGroup):
    date = State()
    time = State()


start = Router()
start.include_router(support)

CHAT_ID = '-4137378938'

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
async def start_signing(callback: CallbackQuery):
    try:
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
            timepicker = await create_timepicker(is_today=True)
            date = datetime.now().strftime("%d.%m.%Y")
            await state.update_data(date=date)
            await callback.message.edit_text(
                f'▶️ Вы выбрали дату: <b>{date}</b>\nВыберите временной диапазон:',
                reply_markup=timepicker,
                parse_mode="HTML"
            )
            return
        calendar = SimpleCalendar(
            locale=await get_user_locale(callback.from_user), show_alerts=True, cancel_btn='Назад', today_btn='Сегодня'
        )
        selected, date = await calendar.process_selection(callback, callback_data)
        if date:
            date = date.strftime("%d.%m.%Y")
            date_now = datetime.now().strftime("%d.%m.%Y")
            timepicker = await create_timepicker()
            if date.strip() == date_now.strip():
                timepicker = await create_timepicker(is_today=True)
            if date < date_now:
                await callback.answer('Невозможно забронировать в данный день!')
                await start_signing(callback)
                return
        if selected:
            
            await state.update_data(date=date)
            await callback.message.edit_text(
                f'▶️ Вы выбрали дату: <b>{date}</b>\nВыберите временной диапазон',
                reply_markup=timepicker,
                parse_mode="HTML"
            )
    except AiogramError as e:
        print(e)
        await state.clear()


@start.callback_query(F.data.startswith('time_'))
async def process_time(callback: CallbackQuery, state: FSMContext):
    try:
        hour_now = datetime.now()
        await callback.answer()
        button_data = int(callback.data.split('_')[1])
        data = await state.get_data()
        append_days = []
        if 'times' in data:
            append_days = list(data['times'])
            if button_data in append_days or button_data < hour_now.hour:
                append_days.remove(button_data)
                await state.update_data(times=append_days)
            else:
                append_days.append(button_data)
                await state.update_data(times=append_days)
        else:
            append_days.append(button_data)
            await state.update_data(times=append_days)

        date = data['date']
        date_now = hour_now.strftime("%d.%m.%Y")
        keyboard = await edit_timepicker(data=append_days)
        if date.strip() == date_now.strip():
            keyboard = await edit_timepicker(data=append_days, is_today=True)
        await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=keyboard)
    except AiogramError as e:
        print(e)
        await state.clear()


@start.callback_query(F.data == 'pick_date')
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await start_signing(callback)


@start.callback_query(F.data.startswith('pay'))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        data = await state.get_data()
        callback_data = callback.data.split('_')
        payment_sum = callback_data[1]
        time_range = list(map(int, callback_data[2:]))
        time_range.sort()
        text = f'ℹ️ <b>Информация о бронировании:</b>\n\n📆 Дата бронирования: <b>{data["date"]}</b>\n\n🕔 Время бронирования:\n'
        for i in time_range:
            text += f'  <b>{i}.00 - {i + 1}.00</b>\n'
        text += f'Общая стоимость: <i><b>{payment_sum}</b></i> руб.\n\n'
        text += '➡️ Для продолжения, подтвердите бронирование!'
        keyboard = await approve_reservation()
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    except AiogramError as e:
        print(e)
        await state.clear()


@start.callback_query(F.data == 'approve')
async def process_approve(callback: CallbackQuery, state: FSMContext):
    try:
        # Обработка сообщений пользователя и отправка брони в базу данных
        # Получение данных о брони
        data = await state.get_data()
        date = data['date'].split('.')
        date = f'{date[2]}-{date[1]}-{date[0]}'
        times = '_'.join(str(i) for i in data['times'])
        user_id = callback.message.chat.id

        # Отправка сообщения пользователю
        keyboard = await approve_payment(user_id=user_id)
        await callback.answer()
        await callback.message.delete_reply_markup(inline_message_id=callback.inline_message_id)
        await callback.message.answer('👌 Успешное бронирование!\n\n💸 Пожалуйста, внесите оплату в течение 15 минут по указанным реквизитам и ожидайте ответа Администратора!')
        await bot.send_message(chat_id=CHAT_ID, reply_markup=keyboard, text=callback.message.text.replace('➡️ Для продолжения, подтвердите бронирование!', f'#{user_id}_{date}_{times}'))
        
        # Добавление в базу данных брони пользователя
        await db.register_buy(user_id=int(user_id), date=date, time=times)
        await state.clear()
    except AiogramError as e:
        print(e)
        await state.clear()