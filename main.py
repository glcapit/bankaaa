import os
import asyncio
import logging
import aiosqlite
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from crypto_pay_api import Crypto

# Загрузка токенов
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")

# Инициализация
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
crypto_client = Crypto(token=CRYPTOBOT_TOKEN)

# Инициализация базы данных
async def init_db():
    async with aiosqlite.connect("staking.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0,
                last_update TEXT
            )
        ''')
        await db.commit()

# /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("staking.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, last_update) VALUES (?, ?)",
                         (user_id, datetime.utcnow().isoformat()))
        await db.commit()

    await message.answer(
        "👋 Добро пожаловать в *CryptoStakeBot*!\n\n"
        "💼 Этот бот позволяет:\n"
        "— Пополнить счёт в TON / USDT\n"
        "— Получать 3% годовых на остаток\n"
        "— Следить за балансом\n\n"
        "📲 Используй команду /pay для пополнения."
    )

# /pay
@dp.message_handler(commands=["pay"])
async def pay(message: types.Message):
    user_id = message.from_user.id

    try:
        invoice = crypto_client.create_invoice(
            asset="TON",
            amount=1.5,
            description=f"Пополнение от {user_id}",
            hidden_message="Спасибо за оплату!",
            paid_btn_name="viewItem",
            paid_btn_url="https://t.me/Bankaaa_bot",  
            payload=str(user_id)
        )
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("💰 Оплатить через CryptoBot", url=invoice['result']['pay_url'])
        )
        await message.answer("🔗 Нажмите кнопку для оплаты:", reply_markup=markup)

    except Exception as e:
        logging.error(f"Ошибка создания инвойса: {e}")
        await message.answer("❌ Ошибка при создании инвойса. Проверьте токен.")

# /balance
@dp.message_handler(commands=["balance"])
async def balance(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("staking.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await message.answer(f"💰 Ваш баланс: {row[0]:.2f} монет")
            else:
                await message.answer("❌ Вы ещё не зарегистрированы. Введите /start")

# Запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    executor.start_polling(dp, skip_updates=True)
