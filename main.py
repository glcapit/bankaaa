import asyncio
import os
import logging
import aiosqlite
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

# Инициализация БД
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
async def start(message: Message):
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
        "🔒 Все транзакции проходят через @CryptoBot — безопасно и быстро.\n"
        "📲 Начни с команды /pay чтобы пополнить баланс."
    )

# /deposit
@dp.message_handler(commands=["deposit"])
async def deposit(message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError("Неверный формат")

        amount = float(parts[1])
        user_id = message.from_user.id

        async with aiosqlite.connect("staking.db") as db:
            await db.execute("UPDATE users SET balance = balance + ?, last_update = ? WHERE user_id = ?",
                             (amount, datetime.utcnow().isoformat(), user_id))
            await db.commit()

        await message.answer(f"✅ Баланс пополнен на {amount:.2f} монет.")
    except ValueError:
        await message.answer("❌ Неверный формат. Используй: /deposit 100")

# /balance
@dp.message_handler(commands=["balance"])
async def balance(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("staking.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await message.answer(f"💰 Ваш баланс: {row[0]:.2f} монет")
            else:
                await message.answer("❌ Вы ещё не зарегистрированы. Введите /start")

# /pay
@dp.message_handler(commands=["pay"])
async def pay(message: Message):
    user_id = message.from_user.id

    async with aiosqlite.connect("staking.db") as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if not await cursor.fetchone():
                await message.answer("❌ Вы ещё не зарегистрированы. Введите /start")
                return

    try:
        invoice_url = await create_invoice(user_id)
        btn = InlineKeyboardMarkup().add(
            InlineKeyboardButton("💰 Оплатить через CryptoBot", url=invoice_url)
        )
        await message.answer("🔗 Нажмите кнопку для оплаты:", reply_markup=btn)
    except Exception as e:
        logging.error(f"Ошибка при создании инвойса: {e}")
        await message.answer(f"❌ Ошибка при создании инвойса: {e}")

# Асинхронное создание инвойса
async def create_invoice(user_id: int) -> str:
    url = "https://pay.crypt.bot/api/v1/invoice/create" 
    headers = {
        "Content-Type": "application/json",
        "Crypto-Pay-API-Token": 374276:AAUwtjaKFaw0lqM8rG1IobOfn74t1bZaQSO
    }
    payload = {
        "asset": "TON",
        "amount": "1.5",
        "description": f"Пополнение баланса от {user_id}",
        "hidden_message": "Спасибо за оплату!",
        "paid_btn_name": "viewItem",
        "paid_btn_url": "https://t.me/Bankaaa_bot",  
        "payload": str(user_id)
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            result = await resp.json()
            if result.get("ok"):
                return result["result"]["pay_url"]
            raise Exception(result.get("error", "Unknown error"))

# Запуск
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init_db())
    try:
        executor.start_polling(dp, skip_updates=True)
    except TerminatedByOtherGetUpdates:
        logging.warning("⚠️ Бот уже запущен где-то ещё.")
