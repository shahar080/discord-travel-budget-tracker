import asyncio

import discord
from discord.ext import commands

import config
from commands import setup as setup_commands
from database import db

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user.name} is online!")
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
