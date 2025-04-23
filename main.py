import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")

bot = Bot(token=API_TOKEN)
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

# Приветствие
@dp.message_handler(commands=['start'])
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
        "📲 Начни с команды /pay чтобы пополнить баланс.",
        parse_mode='Markdown'
    )

# Пополнение вручную
@dp.message_handler(commands=['deposit'])
async def deposit(message: Message):
    try:
        amount = float(message.text.split()[1])
        user_id = message.from_user.id
        async with aiosqlite.connect("staking.db") as db:
            await db.execute("UPDATE users SET balance = balance + ?, last_update = ? WHERE user_id = ?", 
                             (amount, datetime.utcnow().isoformat(), user_id))
            await db.commit()
        await message.answer(f"✅ Баланс пополнен на {amount:.2f} монет.")
    except:
        await message.answer("❌ Неверный формат. Используй: /deposit 100")

# Проверка баланса
@dp.message_handler(commands=['balance'])
async def balance(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("staking.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await message.answer(f"💰 Ваш баланс: {row[0]:.2f} монет")
            else:
                await message.answer("❌ Вы еще не зарегистрированы. Введите /start")

# Создание инвойса через CryptoBot
def create_invoice(user_id: int) -> str:
    url = "https://pay.crypt.bot/createInvoice"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CRYPTOBOT_TOKEN}"
    }
    data = {
        "asset": "TON",
        "amount": "1.5",
        "currency": "TON",
        "description": f"Пополнение баланса от {user_id}",
        "hidden_message": "Спасибо за оплату!",
        "paid_btn_name": "viewItem",
        "paid_btn_url": "https://t.me/YourBot",  # Заменить на ссылку на бота
        "payload": str(user_id)
    }
    response = requests.post(url, headers=headers, json=data)
    invoice = response.json()
    return invoice["result"]["pay_url"]

# Команда оплаты
@dp.message_handler(commands=['pay'])
async def pay(message: Message):
    user_id = message.from_user.id
    invoice_url = create_invoice(user_id)
    btn = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💰 Оплатить через CryptoBot", url=invoice_url)
    )
    await message.answer("🔗 Нажмите кнопку для оплаты:", reply_markup=btn)

# Запуск бота
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init_db())
    executor.start_polling(dp, skip_updates=True)

def create_invoice(user_id: int) -> str:
    url = "https://pay.crypt.bot/createInvoice"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CRYPTOBOT_TOKEN}"
    }
    data = {
        "asset": "TON",
        "amount": "1.5",
        "currency": "TON",
        "description": f"Пополнение баланса от {user_id}",
        "hidden_message": "Спасибо за оплату!",
        "paid_btn_name": "viewItem",
        "paid_btn_url": "https://t.me/YourBot",
        "payload": str(user_id)
    }
    response = requests.post(url, headers=headers, json=data)
    invoice = response.json()
    print("🔍 Ответ от CryptoBot:", invoice)  # 🔍 Добавим лог
    return invoice["result"]["pay_url"]
