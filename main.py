import discord
import re
import os
from discord import app_commands
from discord.ext import commands
from rcon import Client

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from discordAutoBot.BetaApplicationModal import BetaApplicationModal
from discordAutoBot.DiscordConstants import NOOB_ROLE_ID, STAFF_BOT_CHANNEL_ID, GUILD_ID, server_host, \
    server_port, server_password, GETTING_STARTED_CHANNEL_ID, BOT_COMMANDS_CHANNEL_ID, MEMBER_ROLE_ID
from discordAutoBot.JoinWhitelistGuide import setup_embed_on_load, ApplyView, HOW_TO_TITLE

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable the message content intent if needed
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
GUILD = discord.Object(id=GUILD_ID)

@bot.event
async def on_ready():
    synced_commands = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'We have logged in as {bot.user.name} with {len(synced_commands)} commands. Registered {synced_commands}')
    # Ensure the How-To Apply message exists in the staff/bot channel. If not, post it and register the persistent view.
    await setup_embed_on_load(bot)


@bot.tree.command(name="join", description="Apply to join the whitelist!")
@app_commands.guilds(GUILD)
@app_commands.describe(username="Your Minecraft username (case-sensitive)")
async def join_beta(interaction: discord.Interaction, username: str):
    print(f'Applied to server: {username}')
    await interaction.response.send_modal(BetaApplicationModal(username))


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # 1) only care about our staff-review channel
    if payload.channel_id != STAFF_BOT_CHANNEL_ID:
        return
    # 2) ignore the bot itself
    if payload.user_id == bot.user.id:
        return

    # 3) fetch the message & embed
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if not message.embeds:
        return
    embed = message.embeds[0]

    # 4) parse out the Discord user and the Minecraft username
    user_field = embed.fields[0].value  # e.g. "<@1234567890>"
    mc_username = embed.fields[1].value  # as you stored in rq.add_field(name="Username",…)

    match = re.match(r"<@!?(\d+)>", user_field)
    if not match:
        return
    discord_user_id = int(match.group(1))

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(discord_user_id)
    role = guild.get_role(MEMBER_ROLE_ID)

    # 5) Approval path
    if str(payload.emoji) == "✅":
        # 5a) run RCON whitelist command
        response = whitelist_player(server_host, server_port, server_password, mc_username)
        if not response:
            response = "Success!"

        # 5b) give them the Whitelisted role
        if member and role:
            await member.add_roles(role, reason="Samsara whitelist approved")

        # 5b-2) set their nickname to their MC username
        if member:
            try:
                await member.edit(nick=mc_username, reason="Set nickname to Minecraft username on whitelist acceptance")
            except Exception as e:
                print(f"Failed to set nickname: {e}")

        # 5c) DM confirmation with a link to #getting-started
        try:
            getting_started_mention = f"<#{GETTING_STARTED_CHANNEL_ID}>"
            await member.send(
                f"🎉 Congrats **{mc_username}**! You’re application has been accepted.\n"
                f"Head over to {getting_started_mention} to get acquainted with the server!\n"
                f"We're thrilled to have you, let us know if theres anything we can do to help 🧙‍♂️"
            )
        except discord.Forbidden:
            pass

        # 5d) announce in #bot-commands that we’ve accepted them
        try:
            bot_commands = bot.get_channel(BOT_COMMANDS_CHANNEL_ID)
            accept_embed = discord.Embed(
                title="✅ Application Accepted",
                description=f"{member.mention} your application for account '`{mc_username}`' has been accepted!",
                color=0x2ECC71
            )
            await bot_commands.send(embed=accept_embed)
        except Exception as e:
            print("Failed to announce acceptance:", e)

    # 6) Denial path
    elif str(payload.emoji) == "❌":
        if member:
            try:
                await member.send(
                    f"❌ Sorry, your whitelist request for **{mc_username}** was denied."
                )
            except discord.Forbidden:
                pass


#@bot.command(name='whitelist')
async def whitelist(ctx, username):
    print(f'Whitelisting {username}')
    response = whitelist_player(server_host, server_port, server_password, username)
    if not response:
        response = "Success!"
    # You can add more logic here, such as sending a confirmation message
    await ctx.send(f'!whitelist {username} executed. {response}')


def whitelist_player(rcon_host, rcon_port, rcon_password, player_name):
    # Connect to the Minecraft server using RCON
    with Client(rcon_host, rcon_port, passwd=rcon_password) as client:
        # Whitelist the player
        response = client.run(f'whitelist add {player_name}')
        print("Response: " + response)
        return response


# @bot.command(name='whitelistbedrock')
async def whitelist_bedrock(ctx, xuid):
    # https://mcprofile.io/ xuid from gamertag
    print(f'Whitelisting on bedrock {xuid}')
    response = whitelist_bedrock_player(server_host, server_port, server_password, xuid)
    if not response:
        response = "Success!"
    # You can add more logic here, such as sending a confirmation message
    await ctx.send(f'!whitelistbedrock {xuid} executed. {response}')


def whitelist_bedrock_player(rcon_host, rcon_port, rcon_password, xuid):
    # Connect to the Minecraft server using RCON
    with Client(rcon_host, rcon_port, passwd=rcon_password) as client:
        # Whitelist the player
        response = client.run(f'fwhitelist add {hex_xuid_to_uuid(xuid)}')
        print("Response:" + response)
        return response


def hex_xuid_to_uuid(hex_xuid):
    if len(hex_xuid) != 16:
        raise ValueError("Invalid XUID length")
    return f"00000000-0000-0000-{hex_xuid[:4]}-{hex_xuid[4:]}"


if __name__ == '__main__':
    # Run the bot with the bot token from environment
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not set. Set it as an environment variable or in a .env file.")
    bot.run(token)
