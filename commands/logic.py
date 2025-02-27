import logging
import re
from collections import defaultdict

import discord

from db.database import db
from utils import config
from utils.common_funcs import format_time
from views.ConfirmationView import ConfirmationView

logger = logging.getLogger(__name__)


##### General #####
def is_allowed_user(interaction: discord.Interaction) -> bool:
    is_allowed = interaction.user.id in config.ALLOWED_IDS
    if is_allowed is False:
        logger.warning(f"Received request from unauthorized user! {interaction}")
    return is_allowed


##### Spent #####
async def perform_spent(interaction: discord.Interaction, amount: float, currency: str, description: str):
    success = await db.add_expense(interaction.user.id, amount, currency.upper(), description)
    if success is None:
        await interaction.response.send_message("⚠️ Please set your location first using `/location <location>`.",
                                                ephemeral=True)
    elif success is False:
        await interaction.response.send_message("⚠️ Invalid currency. Use a supported currency code.",
                                                ephemeral=True)
    else:
        await interaction.response.send_message(
            f"✅ Recorded: {amount} {currency.upper()} for {description} (converted to ILS).")


##### Total #####
async def perform_total(interaction: discord.Interaction, _location: str = None, _group_by: str = None):
    # If no grouping/filter option is provided, use the existing total.
    if not _group_by:
        total_spent = await db.get_total_spent(interaction.user.id, _location.lower() if _location else None)
        if _location:
            await interaction.response.send_message(
                f"💰 You have spent a total of {total_spent:.2f} ILS in {_location}."
            )
        else:
            await interaction.response.send_message(f"💰 You have spent a total of {total_spent:.2f} ILS overall.")
        return

    # Validate _group_by option.
    valid_literals = {"yyyy", "mm/yy"}
    if _group_by not in valid_literals and not (
            re.match(r"^\d{4}$", _group_by) or re.match(r"^\d{2}/\d{2}$", _group_by)
    ):
        await interaction.response.send_message(
            "❌ Invalid grouping option. Use 'yyyy' or 'mm/yy', or pass a valid year (e.g., 2025) or month/year (e.g., 05/25)."
        )
        return

    # Retrieve all expenses via breakdown.
    _breakdown = await db.get_breakdown(interaction.user.id, _location.lower() if _location else None)
    if not _breakdown:
        message = f"💰 No expenses recorded for **{_location}**." if _location else "💰 No expenses recorded yet."
        await interaction.response.send_message(message)
        return

    # Two scenarios:
    # 1. _group_by is a literal grouping option ("yyyy" or "mm/yy")
    # 2. _group_by is a specific filter (e.g., "2025" or "05/25")
    if _group_by in valid_literals:
        # Use your group_expenses helper to group all expenses accordingly.
        grouped_expenses = group_expenses(_breakdown, _group_by, _location)
        response = f"💰 **Total Spent Breakdown{' for ' + _location if _location else ''}:**\n"
        grand_total = 0

        if not grouped_expenses:
            await interaction.response.send_message(f"💰 No expenses match the filter '{_group_by}'.")
            return

        # For each group (e.g., each year or month/year)
        for key, expenses in grouped_expenses.items():
            group_total = sum(exp["amount"] for exp in expenses)
            response += f"**{key}:** {group_total:.2f} ILS\n"
            grand_total += group_total
        response += f"\n**Grand Total:** {grand_total:.2f} ILS"
        await interaction.response.send_message(response)
    else:
        # _group_by is a specific filter (e.g., "2025" or "05/25")
        # Filter expenses by the specified literal, then group by location.
        filtered_breakdown = {}
        for loc, expenses in _breakdown.items():
            if _location and loc.lower() != _location.lower():
                continue
            filtered = []
            for expense in expenses:
                dt = expense["timestamp"]
                if re.match(r"^\d{4}$", _group_by):  # specific year filter
                    if dt.strftime("%Y") == _group_by:
                        filtered.append(expense)
                elif re.match(r"^\d{2}/\d{2}$", _group_by):  # specific month/year filter
                    if dt.strftime("%m/%y") == _group_by:
                        filtered.append(expense)
            if filtered:
                filtered_breakdown[loc] = filtered

        if not filtered_breakdown:
            await interaction.response.send_message(f"💰 No expenses match the filter '{_group_by}'.")
            return

        response = f"💰 **Total Spent Breakdown{' for ' + _location if _location else ''}:**\n"
        response += f"**{_group_by}:**\n"
        grand_total = 0
        for loc, expenses in filtered_breakdown.items():
            group_total = sum(exp["amount"] for exp in expenses)
            response += f"**{loc}:** {group_total:.2f} ILS\n"
            grand_total += group_total
        response += f"\n**Grand Total:** {grand_total:.2f} ILS"
        await interaction.response.send_message(response)


##### Breakdown #####
def get_group_key(expense_dt, group_by):
    """
    Returns a grouping key based on the group_by parameter.
    For literal grouping ("yyyy" or "mm/yy"), it returns the corresponding formatted string.
    """
    if group_by == "yyyy":
        return expense_dt.strftime("%Y")
    elif group_by == "mm/yy":
        return expense_dt.strftime("%m/%y")
    else:
        return format_time(expense_dt)


def group_expenses(expenses_dict, group_by, specific_location=None):
    """
    Groups expenses by year or month/year. If group_by is a literal "yyyy" or "mm/yy",
    then all matching expenses are grouped accordingly.
    If group_by is a specific filter (e.g., "2025" or "05/25"), then only expenses matching
    that filter are added.
    """
    grouped = defaultdict(list)
    for loc, expenses in expenses_dict.items():
        if specific_location and loc.lower() != specific_location.lower():
            continue
        for expense in expenses:
            dt = expense["timestamp"]
            # When group_by is a literal option, group all expenses accordingly.
            if group_by in {"yyyy", "mm/yy"}:
                key = get_group_key(dt, group_by)
                expense['location'] = loc
                grouped[key].append(expense)
            # Otherwise, treat group_by as a specific filter.
            else:
                if re.match(r"^\d{4}$", group_by):  # specific year, e.g., "2025"
                    key = dt.strftime("%Y")
                    if key == group_by:
                        expense['location'] = loc
                        grouped[key].append(expense)
                elif re.match(r"^\d{2}/\d{2}$", group_by):  # specific month/year, e.g., "05/25"
                    key = dt.strftime("%m/%y")
                    if key == group_by:
                        expense['location'] = loc
                        grouped[key].append(expense)
    return grouped


def format_expense(expense):
    formatted_dt = format_time(expense['timestamp'])
    return f"* {expense['amount']:.2f} ILS on {formatted_dt} ({expense['original_amount']} {expense['currency']})\n"


def calculate_total(expenses):
    return sum(expense["amount"] for expense in expenses)


async def perform_breakdown(interaction: discord.Interaction, _location: str = None, _group_by: str = None):
    async def _breakdown_no_grouping():
        if _location:
            total_ils = sum(exp["amount"] for exp in _breakdown.get(_location.lower(), []))
            response = f"📊 **Expense Breakdown for {_location}:**\n"
            for expense in _breakdown.get(_location.lower(), []):
                formatted = format_time(expense['timestamp'])
                response += f"* {expense['amount']:.2f} ILS on {formatted} ({expense['original_amount']} {expense['currency']})\n"
            response += f"**Total**: {total_ils:.2f} ILS\n"
        else:
            response = "📊 **Expense Breakdown:**\n"
            total_ils = 0
            for loc, expenses in _breakdown.items():
                response += f"**{loc}:**\n"
                for expense in expenses:
                    formatted = format_time(expense['timestamp'])
                    response += f"* {expense['amount']:.2f} ILS on {formatted} ({expense['original_amount']} {expense['currency']})\n"
                    total_ils += expense['amount']
                response += f"**Total**: {total_ils:.2f} ILS\n"
        await interaction.response.send_message(response)

    async def _group_by_literals():
        # Group expenses by literal (_group_by) first.
        grouped_expenses = group_expenses(_breakdown, _group_by, _location)
        _response = f"📊 **Expense Breakdown{' for ' + _location if _location else ''}:**\n"
        _grand_total = 0

        # If no expenses were grouped, show a message.
        if not grouped_expenses:
            await interaction.response.send_message(f"📊 No expenses match the filter '{_group_by}'.")
            return

        # For each literal group (e.g. "2025" or "05/25")
        for literal_key, literal_expenses in grouped_expenses.items():
            _response += f"**{literal_key}:**\n"
            # If no specific location was provided, further group by location.
            if not _location:
                # Group by location using a temporary dict.
                location_group = {}
                for _expense in literal_expenses:
                    # Assumes each expense has a "location" field.
                    _loc = _expense.get("location", "Unknown")
                    location_group.setdefault(_loc, []).append(_expense)
                for _loc, loc_expenses in location_group.items():
                    _response += f"**{_loc}:**\n"
                    for _expense in loc_expenses:
                        _response += format_expense(_expense)
                    _group_total = calculate_total(loc_expenses)
                    _response += f"**Subtotal:** {_group_total:.2f} ILS\n\n"
                    _grand_total += _group_total
            else:
                # If a specific location is provided, just list the expenses.
                for _expense in literal_expenses:
                    _response += format_expense(_expense)
                _group_total = calculate_total(literal_expenses)
                _response += f"**Subtotal:** {_group_total:.2f} ILS\n\n"
                _grand_total += _group_total

        _response += f"**Grand Total:** {_grand_total:.2f} ILS\n"
        await interaction.response.send_message(_response)

    def _group_by_location():
        _filtered_breakdown = {}
        for _loc, _expenses in _breakdown.items():
            if _location and _loc.lower() != _location.lower():
                continue
            filtered = []
            for _expense in _expenses:
                dt = _expense["timestamp"]
                if re.match(r"^\d{4}$", _group_by):  # specific year filter
                    if dt.strftime("%Y") == _group_by:
                        filtered.append(_expense)
                elif re.match(r"^\d{2}/\d{2}$", _group_by):  # specific month/year filter
                    if dt.strftime("%m/%y") == _group_by:
                        filtered.append(_expense)
            if filtered:
                _filtered_breakdown[_loc] = filtered
        return _filtered_breakdown

    _breakdown = await db.get_breakdown(interaction.user.id, _location.lower() if _location else None)
    if not _breakdown:
        message = f"📊 No expenses recorded for **{_location}**." if _location else "📊 No expenses recorded yet."
        await interaction.response.send_message(message)
        return

    # No grouping/filter option provided: use default behavior.
    if not _group_by:
        await _breakdown_no_grouping()
        return

    # Check if _group_by is a literal grouping option ("yyyy" or "mm/yy")
    valid_literals = {"yyyy", "mm/yy"}
    if _group_by in valid_literals:
        await _group_by_literals()
        return

    # Otherwise, _group_by is a specific filter (e.g., "2025" or "05/25")
    # Validate that it matches a 4-digit year or a mm/yy format.
    if not (re.match(r"^\d{4}$", _group_by) or re.match(r"^\d{2}/\d{2}$", _group_by)):
        await interaction.response.send_message(
            "❌ Invalid grouping option. Use 'yyyy' or 'mm/yy', or pass a valid year (e.g., 2025) or month/year (e.g., 05/25)."
        )
        return

    # Filter expenses by the specific _group_by value, grouping them by location.
    filtered_breakdown = _group_by_location()

    if not filtered_breakdown:
        await interaction.response.send_message(f"📊 No expenses match the filter '{_group_by}'.")
        return

    # Build the response with a top-level header for the filter, then group by location.
    response = "📊 **Expense Breakdown:**\n"
    response += f"**{_group_by}:**\n"
    grand_total = 0
    for loc, expenses in filtered_breakdown.items():
        response += f"**{loc}:**\n"
        for expense in expenses:
            response += format_expense(expense)
        group_total = calculate_total(expenses)
        response += f"**Subtotal:** {group_total:.2f} ILS\n\n"
        grand_total += group_total
    response += f"**Grand Total:** {grand_total:.2f} ILS\n"
    await interaction.response.send_message(response)


##### Location #####
async def perform_location(interaction: discord.Interaction, place: str = None):
    if place:
        await db.set_location(interaction.user.id, place.lower())
        await interaction.response.send_message(f"📍 Location set to {place}!")
    else:
        current_location = await db.get_location(interaction.user.id)
        await interaction.response.send_message(f"📍 Current location is set to {current_location}!")


##### Delete #####
async def perform_delete(interaction: discord.Interaction, expense_id: str):
    # Ownership validation.
    expense = await db.get_expense_by_id(interaction.user.id, expense_id)
    if not expense:
        await interaction.response.send_message("❌ Expense not found or you don't have permission to delete it.",
                                                ephemeral=True)
        return

    # Ask for confirmation.
    view = ConfirmationView(timeout=30.0)
    await interaction.response.send_message(
        f"Are you sure you want to delete expense ID {expense_id} (Description: {expense['description']})?",
        view=view,
        ephemeral=True
    )

    await view.wait()

    # If the view timed out without a response.
    if view.value is None:
        await interaction.followup.send("⏰ Confirmation timed out. Deletion cancelled.", ephemeral=True)
        return

    # If the user cancelled.
    if view.value is False:
        await interaction.followup.send("❌ Deletion cancelled.", ephemeral=True)
        return

    # Delete the expense.
    deletion_success = await db.delete_expense(interaction.user.id, expense_id)
    if deletion_success:
        await interaction.followup.send("✅ Expense deleted successfully.", ephemeral=True)
    else:
        await interaction.followup.send("❌ An error occurred while deleting the expense.", ephemeral=True)


##### List #####
async def perform_list_expenses(interaction: discord.Interaction, _filter: str = None):
    # Retrieve all expenses breakdown for the user.
    _breakdown = await db.get_breakdown(interaction.user.id, requires_id=True)
    if not _breakdown:
        await interaction.response.send_message("📊 No expenses recorded yet.", ephemeral=True)
        return

    # If no filter is provided, list all expenses grouped by location.
    if not _filter:
        response = "📊 **All Expenses:**\n"
        for loc, expenses in _breakdown.items():
            response += f"**{loc}:**\n"
            for expense in expenses:
                formatted = format_time(expense['timestamp'])
                response += f"* [{expense['id']}] {expense['amount']:.2f} ILS on {formatted} ({expense['original_amount']} {expense['currency']})\n"
        await interaction.response.send_message(response)
        return

    # Validate _filter: must be a 4-digit year or a mm/yy string.
    if not (re.match(r"^\d{4}$", _filter) or re.match(r"^\d{2}/\d{2}$", _filter)):
        await interaction.response.send_message(
            "❌ Invalid filter. Use a 4-digit year (e.g., 2025) or month/year (e.g., 05/25).", ephemeral=True
        )
        return

    # Filter expenses based on _filter.
    filtered_breakdown = {}
    for loc, expenses in _breakdown.items():
        filtered = []
        for expense in expenses:
            dt = expense["timestamp"]
            if re.match(r"^\d{4}$", _filter):
                if dt.strftime("%Y") == _filter:
                    filtered.append(expense)
            elif re.match(r"^\d{2}/\d{2}$", _filter):
                if dt.strftime("%m/%y") == _filter:
                    filtered.append(expense)
        if filtered:
            filtered_breakdown[loc] = filtered

    if not filtered_breakdown:
        await interaction.response.send_message(f"📊 No expenses match the filter '{_filter}'.", ephemeral=True)
        return

    # Build the response, grouping by location.
    response = f"📊 **Expenses for {_filter}:**\n"
    for loc, expenses in filtered_breakdown.items():
        response += f"**{loc}:**\n"
        for expense in expenses:
            formatted = format_time(expense['timestamp'])
            response += f"* [{expense['id']}] {expense['amount']:.2f} ILS on {formatted} ({expense['original_amount']} {expense['currency']})\n"
    await interaction.response.send_message(response)
