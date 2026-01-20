import discord
from discord import ui, TextStyle

from discordAutoWhitelistSamsara.DiscordConstants import STAFF_BOT_CHANNEL_ID


class BetaApplicationModal(ui.Modal, title="Beta Application"):
    username = ui.TextInput(
        label="Minecraft Username",
        placeholder="EthosLab (to be whitelisted)",
        required=True,
        max_length=16
    )
    age = ui.TextInput(
        label="How old are you?",
        style=TextStyle.short,
        placeholder="11d7",
        required=False,
        max_length=2
    )
    discovery = ui.TextInput(
        label="How did you hear about us?",
        style=TextStyle.short,
        placeholder="Friend/Reddit/Youtube/etc",
        required=True,
        max_length=80
    )
    experience = ui.TextInput(
        label="How long have you been playing minecraft?",
        style=TextStyle.short,
        placeholder="Since pre-alpha!",
        required=True,
        max_length=300
    )
    reason = ui.TextInput(
        label="Why do you want to join?",
        style=TextStyle.short,
        placeholder="I love epic survival worlds...",
        required=True,
        max_length=300
    )

    def __init__(self, mc_username: str):
        super().__init__()
        # override the class‐defined field’s default
        self.username.default = mc_username

    async def on_submit(self, interaction: discord.Interaction):
        # this runs when they hit “Submit”
        # you now have self.username.value, self.age.value, self.reason.value
        # send to staff channel just like before:
        staff = interaction.client.get_channel(STAFF_BOT_CHANNEL_ID)
        embed = discord.Embed(
            title="📝 Beta Application",
            color=0x3498DB
        )
        embed.add_field(name="Discord User", value=interaction.user.mention, inline=False)
        embed.add_field(name="Minecraft Username", value=self.username.value, inline=True)
        if self.age.value:
            embed.add_field(name="Age", value=self.age.value, inline=True)
        embed.add_field(name="Discovery", value=self.discovery.value, inline=False)
        embed.add_field(name="Experience", value=self.experience.value, inline=False)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)

        msg = await staff.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        embed = discord.Embed(
            title="Beta Application Received",
            description=(
                f"🎉 Thanks {interaction.user.mention}!  \n"
                f"We’ve received your request for **{self.username.value}**."
            ),
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)