import asyncio
import logging

import discord
from discord.ext import commands

from commands.bot_commands import setup as setup_commands
from db.database import db
from utils import config

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@bot.event
async def on_ready():
    logger.info(f"{bot.user.name} is online!")
    await bot.tree.sync()


async def setup():
    await db.connect()
    await db.create_tables()
    await setup_commands(bot)


async def main():
    await setup()
    await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
