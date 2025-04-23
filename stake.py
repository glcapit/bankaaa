import aiosqlite
from datetime import datetime
import asyncio

INTEREST_RATE = 0.03  # 3% годовых
SECONDS_IN_YEAR = 365 * 24 * 60 * 60

async def stake_accrual():
    async with aiosqlite.connect("staking.db") as db:
        async with db.execute("SELECT user_id, balance, last_update FROM users") as cursor:
            rows = await cursor.fetchall()
            for user_id, balance, last_update in rows:
                delta_seconds = (datetime.utcnow() - datetime.fromisoformat(last_update)).total_seconds()
                interest = balance * (INTEREST_RATE * delta_seconds / SECONDS_IN_YEAR)
                new_balance = balance + interest
                await db.execute("UPDATE users SET balance = ?, last_update = ? WHERE user_id = ?", 
                                 (new_balance, datetime.utcnow().isoformat(), user_id))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(stake_accrual())
