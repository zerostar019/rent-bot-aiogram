from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from handlers.keyboard.timepicker import help_menu, return_to_menu, return_to_help_menu
from handlers.keyboard.support_kb import approve_payment_timeout
from handlers.keyboard.support_kb import (
    create_support_button,
    cancel_enter
)
from bot.bot_instance import bot
from database.database import db
from aiogram.exceptions import AiogramError


class UserQuery(StatesGroup):
    user_id = State()
    message_id = State()
    answer = State()

class AnswerRoom(StatesGroup):
    user_id = State()
    message_id = State()
    answer = State()


support = Router()

CHAT_ID = '-4190920965'


SUPPORT_TEXT = 'ℹ️ Администратор ответит Вам в ближайшее время!\n\nПожалуйста, напишите Ваш вопрос👇'


@support.callback_query(F.data == 'info')
async def show_info(callback: CallbackQuery):
    keyboard = await help_menu()
    await callback.message.edit_text('ℹ️ Выберите, интересующую Вас информацию!', reply_markup=keyboard)

@support.callback_query(F.data == 'rules')
async def show_rules(callback: CallbackQuery):
    keyboard = await return_to_help_menu()
    text = '''БРОНИРУЯ АПАРТАМЕНТЫ, ВЫ СОГЛАШАЕТЕСЬ СОБЛЮДАТЬ
📍 минимальное время бронирование – 2 часа
📍 подтверждением бронирования номера является 100% предоплата
📍 стоимость аренды апартаментов рассчитана для 2 гостей. доплата за каждого дополнительного гостя – 5 000 ₽. в апартаментах могут одновременно находиться не более 4 человек
📍 владельцы апартаментов не несут ответственность за ущерб, причинённый здоровью и имуществу гостей из-за неправильного использования ими оборудования, аксессуаров и мебели
📍 если гости покидают номер раньше истечения времени, деньги за неиспользованное время не возвращаются
📍 при повреждении или поломке оборудования, аксессуаров или мебели администрация вправе взыскать с гостя их полную стоимость
📍 запрещено курение, вейпы, кальяны и любые другие виды табачной продукции, а также чрезмерное употребление алкогольных напитков, употребление наркотических средств.
📍 запрещен вход с оружием или животными
📍 запрещена передача апартаментов в субаренду или другое их коммерческое использование'''
    await callback.message.edit_text(text=text, reply_markup=keyboard)


@support.callback_query(F.data == '_pay_rules')
async def show_pay_rules(callback: CallbackQuery):
    keyboard = await return_to_help_menu()
    text = 'Реквизиты для оплаты появятся здесь после брони.'
    await callback.message.edit_text(text=text, reply_markup=keyboard)


@support.callback_query(F.data == 'location')
async def show_location(callback: CallbackQuery):
    keyboard = await return_to_help_menu()
    text = 'ул. Улица 69, ЖК Лазурные Небеса'
    await callback.message.edit_text(text=text, reply_markup=keyboard)


@support.callback_query(F.data == 'help')
async def call_manager(callback: CallbackQuery):
    keyboard = await return_to_menu()
    await callback.message.edit_text(text=SUPPORT_TEXT, reply_markup=keyboard)


@support.message(F.chat.func(lambda chat: chat.id != int(CHAT_ID)))
async def forward_message(message: Message):
    user_id = message.from_user.id
    msg = message.text
    keyboard = await create_support_button(user_id=user_id)
    await message.reply(text='Пожалуйста, ожидайте, администратор ответит Вам в ближайшее время!')
    text = f"Новое сообщение от #{user_id}\n\n{msg}"
    await bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=keyboard)


@support.callback_query(F.data == 'deny_answer')
async def deny_answer_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()


@support.callback_query(F.data.startswith('user'))
async def start_answer_question_2(callback: CallbackQuery, state: FSMContext):
    await start_answer_question(callback, state)

@support.callback_query(F.data.startswith('answerBook'))
async def start_answer_question(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.data.split('_')[1]
    keyboard = await cancel_enter()
    await state.set_state(UserQuery.answer)
    msg = await callback.message.answer(text=f'Введите текст ответа для {user_id}:', reply_markup=keyboard)
    await state.update_data(user_id=user_id)
    await state.update_data(message_id=msg.message_id)


@support.message(F.chat.func(lambda chat: chat.id == int(CHAT_ID)), UserQuery.answer)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    message_id = data['message_id']
    text = '👤 Администратор:\n\n'
    text += message.text.strip()
    await bot.delete_message(chat_id=CHAT_ID, message_id=message_id)
    await bot.send_message(chat_id=int(user_id), text=text)
    await state.clear()


@support.callback_query(F.data.startswith('approvePay'))
async def process_payment_admin(callback: CallbackQuery):
    try:
        # Ответ администратора при успешной операции бронирования 
        await callback.answer()
        message_data = callback.data.split('_')
        user_id = int(message_data[1])
        reserve_details = callback.message.text.split('#')[1].split('_')
        date = reserve_details[1]
        rent_start = reserve_details[2]
        rent_end = reserve_details[3]
        await db.update_booking_status(user_id=int(user_id), date=date, rent_start=rent_start, rent_end=rent_end)
        keyboard = await approve_payment_timeout(user_id=user_id)
        await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=keyboard)
        text = '✅ Ваша бронь успешно оплачена. Ожидайте, пожалуйста, дальнейших действий от Администратора!'
        text += '\n\nДля обращения к Администратору, просто напишите любое сообщение боту!'
        await bot.send_message(chat_id=user_id, text=text)
    except AiogramError as e:
        print(e)


@support.message(F.chat.func(lambda chat: chat.id == int(CHAT_ID)), AnswerRoom.answer)
async def process_answer_room_admin(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    message_id = data['message_id']
    text = '👤 Администратор:\n\n'
    text += message.text.strip()
    text += '\n\nДля обращения к Администратору, просто напишите любое сообщение боту!'
    await bot.delete_message(chat_id=CHAT_ID, message_id=message_id)
    await bot.send_message(chat_id=int(user_id), text=text)
    await state.clear()