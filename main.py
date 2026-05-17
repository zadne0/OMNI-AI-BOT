import asyncio
import logging
from aiogram import Bot, Dispatcher
from os import getenv
from dotenv import load_dotenv
from handlers.ai import router as ai_router
from utils.db import init_db

load_dotenv()

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=getenv("BOT_TOKEN"))
    dp = Dispatcher()
    
    # Мы подключаем ТОЛЬКО один роутер. Больше ничего!
    dp.include_router(ai_router)
    
    print("🚀 Омни-Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())