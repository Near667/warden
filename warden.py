import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for member management

bot = commands.Bot(command_prefix="!", intents=intents)
warnings = {}  # Simple dict to store warnings: {user_id: warning_count}

LOG_CHANNEL_ID = 1358604923033616638  # Replace with your log channel ID

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot connected as {bot.user}")

async def send_log(message):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(message)

# Kick Command
@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="Member to kick", reason="Reason for kicking")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("⛔ You don't have permission to kick members.", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member.mention} has been kicked for: {reason}")
    await send_log(f"👢 **{member}** was kicked by **{interaction.user}** for: {reason}")

# Ban Command
@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="Member to ban", reason="Reason for banning")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("⛔ You don't have permission to ban members.", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member.mention} has been banned for: {reason}")
    await send_log(f"🔨 **{member}** was banned by **{interaction.user}** for: {reason}")

# Warn Command
@bot.tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="Member to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("⛔ You don't have permission to warn members.", ephemeral=True)
        return
    user_id = member.id
    warnings[user_id] = warnings.get(user_id, 0) + 1
    await interaction.response.send_message(f"⚠️ {member.mention} has been warned. Total warnings: {warnings[user_id]}")
    await send_log(f"⚠️ **{member}** was warned by **{interaction.user}** for: {reason} (Total: {warnings[user_id]})")
    
    if warnings[user_id] >= 3:  # Auto-ban after 3 warnings
        await member.ban(reason="Too many warnings")
        await send_log(f"🚫 **{member}** was auto-banned for exceeding warning limit.")

# Mute Command (Temp Mute)
@bot.tree.command(name="mute", description="Temporarily mute a member")
@app_commands.describe(member="Member to mute", duration="Duration in seconds", reason="Reason for muting")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("⛔ You don't have permission to mute members.", ephemeral=True)
        return
    if not member.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ You cannot mute a moderator or admin.", ephemeral=True)
        return

    await member.timeout(discord.utils.utcnow() + discord.timedelta(seconds=duration), reason=reason)
    await interaction.response.send_message(f"🔇 {member.mention} has been muted for {duration} seconds.")
    await send_log(f"🔇 **{member}** was muted by **{interaction.user}** for {duration} seconds. Reason: {reason}")

# Clear Command
@bot.tree.command(name="clear", description="Clear messages from a channel")
@app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("⛔ You don't have permission to manage messages.", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)
    await send_log(f"🧹 **{interaction.user}** deleted {len(deleted)} messages in {interaction.channel}")

# Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ You don't have permission to do that.", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing a required argument.", ephemeral=True)
    else:
        raise error  # Raise unhandled errors
# Start the bot (don't forget to replace this with your real token)
bot.run(os.getenv("DISCORD_TOKEN"))
