import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import config
from database import db
from typing import Optional


bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==========================================
# FSM
# ==========================================

class JoinGame(StatesGroup):
    waiting_for_code = State()
    waiting_for_name = State()
    waiting_for_wishes = State()

# ==========================================
# Клавиатуры
# ==========================================


def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Создать игру")],
            [KeyboardButton(text="🎯 Присоединиться к игре")],
            [KeyboardButton(text="📋 Моя игра"), KeyboardButton(text="🎁 Кому я дарю?")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True
    )
    return keyboard

def get_organizer_menu(): 
    keyboard = ReplyKeyboardMarkup( 
        keyboard=[ 
            [KeyboardButton(text="👤 Список участников")], 
            [KeyboardButton(text="🎲 Запустить жеребьевку")], 
            [KeyboardButton(text="🏠 Главное меню")],  
        ], 
        resize_keyboard=True
    ) 
    return keyboard
    
def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⛔ Отмена")],
        ],
        resize_keyboard=True
    )
    return keyboard


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для игры в Тайного Санту 🎅\n\n"
        "🎮 <b>Что я умею:</b>\n"
        "• Создавать игры для обмена подарками\n"
        "• Помогать участникам присоединяться\n"
        "• Проводить тайную жеребьёвку\n"
        "• Хранить пожелания к подаркам\n\n"
        "Выбери действие на клавиатуре ⬇️",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
        )
    
@dp.message(Command("create_game"))
@dp.message(F.text == "🎮 Создать игру")
async def create_game(message: Message):
    code = db.create_game(message.from_user.id)
    await message.answer(
        f"🎮 <b>Игра создана!</b>\n\n"
        f"📝 Код игры: <code>{code}</code>\n\n"
        f"Отправьте этот код участникам.\n"
        f"Они смогут присоединиться через кнопку "
        f"'🎯 Присоединиться к игре'\n\n"
        f"⚠️ Для жеребьёвки нужно минимум 3 участника", 
        reply_markup=get_organizer_menu(), 
        parse_mode="HTML"
    )
    
@dp.message(Command("help"))
@dp.message(F.text=="❓ Помощь")
async def help_command(message: Message):
    help_text = """
    <b>Как играть в Тайного Санту (5 шагов):</b>
    1. Создайте игру.
    2. Пригласите друзей.
    3. Запишите свои пожелания.
    4. Дождитесь жеребьёвки.
    5. Купите и подарите подарок!

    <b>Минимальное количество участников:</b> 3
    <b>Правило:</b> Один участник — одна игра.
    <b>Удачи!</b>
    """
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
    
    
# Join game

@dp.message(Command("join_game"))
@dp.message(F.text=="🎯 Присоединиться к игре")
async def join_game_start(message: Message, state: FSMContext):
    await state.set_state(JoinGame.waiting_for_code)
    await message.answer(
        "Введите код игры (6 символов):",
        reply_markup=get_cancel_keyboard()
    )
    
    
# Обработка кода игры


@dp.message(JoinGame.waiting_for_code)
async def process_game_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()

    if message.text == "⛔ Отмена":
        await state.clear()
        await message.answer("⛔ Отменено", reply_markup=get_main_menu())
        return

    if len(code) != 6:
        await message.answer("Код должен содержать 6 символов. Попробуйте снова:")
        return

    game = db.get_game_by_code(code)
    
    if game is None:
        await message.answer("Игра не найдена. Проверьте код и введите снова:")
        return
    
    if game.get("is_drawn"):
        await message.answer("Жеребьёвка уже проведена, присоединиться нельзя.")
        await state.clear()
        await message.answer("Возврат в главное меню.", reply_markup=get_main_menu())
        return

    await state.update_data(game_code=code)
    await state.set_state(JoinGame.waiting_for_name)
    await message.answer(f"Игра найдена! Теперь введите ваше имя:")
    
    
# Обработка имени участника

@dp.message(JoinGame.waiting_for_name)
async def process_participant_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if message.text == "⛔ Отмена":
        await state.clear()
        await message.answer("⛔ Отменено.", reply_markup=get_main_menu())
        return

    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуйте снова:")
        return

    await state.update_data(user_name=name)
    await state.set_state(JoinGame.waiting_for_wishes)
    
    examples = "Например:\n- Книги\n- Сладости\n- Косметика"
    await message.answer(
        f"Привет, {name}!\n"
        f"Расскажите, что бы вы хотели получить в подарок.\n"
        f"{examples}\n"
        f"Если пожеланий нет, отправьте '-'."
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
