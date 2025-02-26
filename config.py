import os

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
EXCHANGE_API_KEY = os.environ.get("EXCHANGE_API_KEY")
ALLOWED_IDS = {int(uid.strip()) for uid in os.environ.get("ALLOWED_IDS", "").split(",") if uid.strip().isdigit()}
