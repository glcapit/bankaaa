from flask import Flask, request
import aiosqlite
import asyncio

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    if not data or data.get("status") != "paid":
        return {"ok": False}

    payload = data.get("payload")  # user_id
    amount = float(data.get("amount", 0))

    if payload and amount > 0:
        asyncio.run(update_balance(int(payload), amount))
        print(f"💸 User {payload} пополнил {amount}")
        return {"ok": True}

    return {"ok": False}

async def update_balance(user_id: int, amount: float):
    async with aiosqlite.connect("staking.db") as db:
        await db.execute("UPDATE users SET balance = balance + ?, last_update = datetime('now') WHERE user_id = ?", (amount, user_id))
        await db.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
