import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers import router
from app.db import init_db
from app.utils import load_valid_tags

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    await init_db()
    await load_valid_tags()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Power off')