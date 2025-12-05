import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import config


bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


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


@dp.Message()
async def echo(message: Message):
    await message.answer(message.text)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("all dead")
