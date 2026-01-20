from discord import ui, ButtonStyle
import discord

from discordAutoWhitelistSamsara.BetaApplicationModal import BetaApplicationModal
from discordAutoWhitelistSamsara.DiscordConstants import JOIN_BETA_CHANNEL_ID

HOW_TO_TITLE = "Apply for Whitelist"

async def setup_embed_on_load(bot: discord.Client):
    try:
        channel = bot.get_channel(JOIN_BETA_CHANNEL_ID)
        if channel is None:
            print(f"HowToGuide: channel {JOIN_BETA_CHANNEL_ID} not found (bot may not be in the guild yet or lacks permissions).")
        else:
            # register persistent view so the button works across restarts
            bot.add_view(ApplyView())

            found = False
            async for msg in channel.history(limit=100):
                if msg.author == bot.user and msg.embeds:
                    emb = msg.embeds[0]
                    if emb.title == HOW_TO_TITLE:
                        print("HowToGuide: how-to message already exists in channel")
                        found = True
                        break

            if not found:
                try:
                    await channel.send(embed=get_embed(), view=ApplyView())
                    print("HowToGuide: posted how-to message in staff channel")
                except discord.Forbidden:
                    print("HowToGuide: missing permission to send messages in the target channel")
                except Exception as e:
                    print("HowToGuide: failed to post how-to message:", e)
    except Exception as e:
        print("HowToGuide: unexpected error while ensuring how-to message:", e)

def get_embed():
    """Return the How-To embed for the whitelist application."""
    embed = discord.Embed(
        title=HOW_TO_TITLE,
        description=(
            "Welcome! If you'd like to join the server, use the button below to open the application form.\n\n"
            "Please enter your Minecraft username and answer the short questions. Staff will review your application promptly.\n\n"
        ),
        color=0x3498DB,
    )
    embed.add_field(name="No Essays Required", value="But please answer the questions thoughtfully.", inline=False)
    embed.add_field(name="Usernames are Case-Sensitive!", value="Make sure your Minecraft username is capitalized and spelled correctly.", inline=False)
    embed.set_footer(text="If you have trouble applying, contact staff.")
    return embed


class ApplyView(ui.View):
    """Persistent view with an Apply button that opens the BetaApplicationModal."""

    def __init__(self):
        # timeout=None makes the view persistent across restarts (when re-registered)
        super().__init__(timeout=None)

    @ui.button(label="Apply", style=ButtonStyle.primary, custom_id="howto_apply_button")
    async def apply_button(self, interaction: discord.Interaction, button: ui.Button):
        # Open the modal for the applicant. We don't have a prefilled username here.
        await interaction.response.send_modal(BetaApplicationModal(""))
