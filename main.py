import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.operation import router as operation_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(operation_router)
    dp.include_router(start_router)

    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())