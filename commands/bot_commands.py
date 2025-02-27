import logging

import discord
from discord import app_commands
from discord.ext import commands

from commands.logic import perform_spent, perform_total, perform_breakdown, perform_location, perform_delete, \
    perform_list_expenses, is_allowed_user

logger = logging.getLogger(__name__)


class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spent", description="Log an expense")
    @app_commands.describe(amount="Amount spent", currency="Currency code", description="Expense description")
    @app_commands.check(is_allowed_user)
    async def spent(self, interaction: discord.Interaction, amount: float, currency: str, description: str):
        logger.info(
            f"Adding spent for {interaction.user.name}({interaction.user.id}) - Data: amount:{amount}, "
            f"currency: {currency}, description:{description}")
        await perform_spent(interaction, amount, currency, description)

    @app_commands.command(name="total", description="View total spent in ILS")
    @app_commands.describe(
        _location="(Optional) View total spent in a specific location",
        _group_by="(Optional) Group total by 'yyyy' or 'mm/yy', or filter by specific year (e.g., 2025) or month/year (e.g., 05/25)"
    )
    @app_commands.check(is_allowed_user)
    async def total(self, interaction: discord.Interaction, _location: str = None, _group_by: str = None):
        logger.info(
            f"Performing total for {interaction.user.name}({interaction.user.id}) - Data: _location:{_location}, "
            f"_group_by: {_group_by}")
        await perform_total(interaction, _location, _group_by)

    @app_commands.command(name="breakdown", description="View expense breakdown by description")
    @app_commands.describe(
        _location="(Optional) Show breakdown for a specific location",
        _group_by="(Optional) Group breakdown by 'yyyy' or 'mm/yy', or filter by specific year (e.g., 2025) or month/year (e.g., 05/25)"
    )
    @app_commands.check(is_allowed_user)
    async def breakdown(self, interaction: discord.Interaction, _location: str = None, _group_by: str = None):
        logger.info(
            f"Performing breakdown for {interaction.user.name}({interaction.user.id}) - Data: _location:{_location}, "
            f"_group_by: {_group_by}")
        await perform_breakdown(interaction, _location, _group_by)

    @app_commands.command(name="location", description="Set your current location")
    @app_commands.describe(place="(Optional) Set current place")
    @app_commands.check(is_allowed_user)
    async def location(self, interaction: discord.Interaction, place: str = None):
        logger.info(
            f"Performing location for {interaction.user.name}({interaction.user.id}) - Data: place:{place}")
        await perform_location(interaction, place)

    @app_commands.command(name="delete_expense", description="Delete an expense by its ID with confirmation")
    @app_commands.describe(expense_id="The ID of the expense to delete")
    @app_commands.check(is_allowed_user)
    async def delete_expense(self, interaction: discord.Interaction, expense_id: str):
        logger.info(f"Deleting for {interaction.user.name}({interaction.user.id}) - Data: expense_id:{expense_id}")
        await perform_delete(interaction, expense_id)

    @app_commands.command(name="list_expenses", description="List all expenses or by specific filters")
    @app_commands.describe(
        _filter="(Optional) filter by specific year (e.g., 2025) or month/year (e.g., 05/25)"
    )
    @app_commands.check(is_allowed_user)
    async def list_expenses(self, interaction: discord.Interaction, _filter: str = None):
        logger.info(
            f"Listing for {interaction.user.name}({interaction.user.id}) - Data: _filter:{_filter}")
        await perform_list_expenses(interaction, _filter)


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
