import discord
from discord import app_commands
from discord.ext import commands

from database import db


class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spent", description="Log an expense")
    @app_commands.describe(amount="Amount spent", currency="Currency code", category="Expense category")
    async def spent(self, interaction: discord.Interaction, amount: float, currency: str, category: str):
        success = await db.add_expense(interaction.user.id, amount, currency.upper(), category)
        if success is None:
            await interaction.response.send_message("⚠️ Please set your location first using `/location <location>`.",
                                                    ephemeral=True)
        elif success is False:
            await interaction.response.send_message("⚠️ Invalid currency. Use a supported currency code.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(
                f"✅ Recorded: {amount} {currency.upper()} for {category} (converted to ILS).")

    @app_commands.command(name="total", description="View total spent in ILS")
    @app_commands.describe(_location="(Optional) View total spent in a specific location")
    async def total(self, interaction: discord.Interaction, _location: str = None):
        total_spent = await db.get_total_spent(interaction.user.id, _location.lower() if _location else None)
        if _location:
            await interaction.response.send_message(
                f"💰 You have spent a total of {total_spent:.2f} ILS in {_location}.")
        else:
            await interaction.response.send_message(f"💰 You have spent a total of {total_spent:.2f} ILS overall.")

    @app_commands.command(name="breakdown", description="View expense breakdown by category")
    @app_commands.describe(_location="(Optional) Show breakdown for a specific location")
    async def breakdown(self, interaction: discord.Interaction, _location: str = None):
        _breakdown = await db.get_breakdown(interaction.user.id, _location.lower() if _location else None)
        if not _breakdown:
            await interaction.response.send_message(
                f"📊 No expenses recorded for **{_location}**." if _location else "📊 No expenses recorded yet.")
            return

        if _location:
            total_ils = sum(exp["amount"] for exp in _breakdown.get(_location.lower(), []))
            response = f"📊 **Expense Breakdown for {_location}:**\n"
            for expense in _breakdown.get(_location.lower(), []):
                response += f"* {expense['amount']:.2f} ILS ({expense['original_amount']} {expense['currency']})\n"
            response += f"**Total**: {total_ils:.2f} ILS\n"
        else:
            response = "📊 **Expense Breakdown:**\n"
            total_ils = 0
            for loc, expenses in _breakdown.items():
                response += f"**{loc}:**\n"
                for expense in expenses:
                    response += f"* {expense['amount']:.2f} ILS ({expense['original_amount']} {expense['currency']})\n"
                    total_ils += expense['amount']
                response += f"**Total**: {total_ils:.2f} ILS\n"

        await interaction.response.send_message(response)

    @app_commands.command(name="location", description="Set your current location")
    @app_commands.describe(place="(Optional) Set current place")
    async def location(self, interaction: discord.Interaction, place: str = None):
        if place:
            await db.set_location(interaction.user.id, place.lower())
            await interaction.response.send_message(f"📍 Location set to {place}!")
        else:
            current_location = await db.get_location(interaction.user.id)
            await interaction.response.send_message(f"📍 Current location is set to {current_location}!")


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
