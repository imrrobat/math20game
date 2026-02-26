import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import main_handlers

# init_db()
load_dotenv()
API = os.getenv("API")


async def main():
    bot = Bot(API)
    dp = Dispatcher()

    dp.include_router(main_handlers.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
