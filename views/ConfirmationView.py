import discord


class ConfirmationView(discord.ui.View):
    success_message: str
    failure_message: str

    def __init__(self, success_message: str = None, failure_message: str = None, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.success_message = success_message
        self.failure_message = failure_message
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        if self.success_message:
            await interaction.response.send_message(self.success_message, ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        if self.failure_message:
            await interaction.response.send_message(self.failure_message, ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True)
