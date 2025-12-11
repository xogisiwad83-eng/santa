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
    


async def main():
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("all dead")
