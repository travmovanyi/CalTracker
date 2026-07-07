import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import start, food, weight


async def main():
    logging.basicConfig(level=logging.INFO)

    if BOT_TOKEN == "ВСТАВ_СЮДИ_СВІЙ_ТОКЕН":
        print(
            "\n⚠️  Токен бота не налаштовано!\n"
            "Відкрий bot/config.py і встав токен, отриманий від @BotFather,\n"
            "або задай змінну середовища BOT_TOKEN.\n"
        )
        return

    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(food.router)
    dp.include_router(weight.router)

    print("Бот запущено. Натисни Ctrl+C для зупинки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
