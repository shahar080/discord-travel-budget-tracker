import asyncpg
import requests

import config


class Database:
    def __init__(self):
        self.db = None
        self.BASE_CURRENCY = "ILS"
        self.EXCHANGE_API_URL = f"https://v6.exchangerate-api.com/v6/{config.EXCHANGE_API_KEY}/latest/"
        self.VALID_CURRENCIES = self.load_valid_currencies()

    async def connect(self):
        if self.db is None:
            self.db = await asyncpg.create_pool(config.DATABASE_URL)

    async def create_tables(self):
        async with self.db.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    amount NUMERIC(10, 2) NOT NULL,
                    currency TEXT NOT NULL,
                    converted_amount NUMERIC(10, 2) NOT NULL,
                    category TEXT NOT NULL,
                    location TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_locations (
                    user_id TEXT PRIMARY KEY,
                    location TEXT NOT NULL
                );
            """)

    async def get_conversion_rate(self, from_currency):
        response = requests.get(f"{self.EXCHANGE_API_URL}{from_currency}")
        data = response.json()
        return data["conversion_rates"].get(self.BASE_CURRENCY, 1.0)

    async def add_expense(self, user_id, amount, currency, category):
        user_location = await self.get_location(user_id)
        if not user_location:
            return None
        if currency.upper() not in self.VALID_CURRENCIES:
            return False
        conversion_rate = await self.get_conversion_rate(currency)
        converted_amount = amount * conversion_rate
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO expenses (user_id, amount, currency, converted_amount, category, location)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, str(user_id), amount, currency.upper(), converted_amount, category, user_location)
        return True

    async def get_total_spent(self, user_id, location=None):
        async with self.db.acquire() as conn:
            if location:
                result = await conn.fetchval("""
                    SELECT SUM(converted_amount) FROM expenses WHERE user_id = $1 AND location ILIKE $2
                """, str(user_id), location)
            else:
                result = await conn.fetchval("""
                    SELECT SUM(converted_amount) FROM expenses WHERE user_id = $1
                """, str(user_id))
        return result if result else 0

    async def get_breakdown(self, user_id, location=None):
        """Get total spent per category, grouped by location, with original currency values."""
        if self.db is None:
            await self.connect()

        async with self.db.acquire() as conn:
            if location:
                rows = await conn.fetch("""
                    SELECT location, amount, currency, converted_amount 
                    FROM expenses WHERE user_id = $1 AND location ILIKE $2 ORDER BY location
                """, str(user_id), location)
            else:
                rows = await conn.fetch("""
                    SELECT location, amount, currency, converted_amount 
                    FROM expenses WHERE user_id = $1 ORDER BY location
                """, str(user_id))

        breakdown = {}
        for row in rows:
            loc = row["location"].lower()
            if loc not in breakdown:
                breakdown[loc] = []
            breakdown[loc].append({
                "amount": row["converted_amount"],
                "original_amount": row["amount"],
                "currency": row["currency"]
            })

        return breakdown

    async def set_location(self, user_id, location):
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_locations (user_id, location)
                VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET location = EXCLUDED.location
            """, str(user_id), location)

    async def get_location(self, user_id):
        async with self.db.acquire() as conn:
            result = await conn.fetchval("""
                SELECT location FROM user_locations WHERE user_id = $1
            """, str(user_id))
        return result

    def load_valid_currencies(self):
        response = requests.get(f"https://v6.exchangerate-api.com/v6/{config.EXCHANGE_API_KEY}/codes")
        data = response.json()
        return {code for code, _ in data.get("supported_codes", [])}


db = Database()
