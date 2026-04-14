import discord
from discord import app_commands
from moderator import classify_message
from image_moderator import classify_image
from url_moderator import analyze_urls, load_blocklist
from config import DISCORD_BOT_TOKEN
from github_sync import sync_example_to_github
from vector_store import add_example
import logging
import asyncio
from prometheus_client import Gauge
from stats import init_db, get_stat, increment_stat, add_group, get_groups_count, get_total_members

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class SusMessageBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        synced = await self.tree.sync()
        logging.info(f"Synced {len(synced)} commands globally")

client = SusMessageBot()
GROUPS_COUNT = Gauge('discord_groups_count_total', 'Number of Discord servers bot is in')
MEMBERS_PROTECTED = Gauge('discord_members_protected_total', 'Total Discord members protected')

@client.event
async def on_ready():
    load_blocklist()
    for guild in client.guilds:
        add_group(guild.id, guild.member_count)
    GROUPS_COUNT.set(get_groups_count())
    MEMBERS_PROTECTED.set(get_total_members())
    logging.info(f"Bot ready — logged in as {client.user}")

@client.event
async def on_guild_join(guild: discord.Guild):
    add_group(guild.id, guild.member_count)
    GROUPS_COUNT.set(get_groups_count())
    MEMBERS_PROTECTED.set(get_total_members())
    logging.info(f"Joined new server: {guild.name} ({guild.id}) with {guild.member_count} members")

    channel = guild.system_channel or next(
        (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None
    )
    if channel:
        await channel.send(
            "👋 Thanks for adding SusMessageBot! I am an AI Anti-Scam Moderation Bot!\n\n"
            "Please ensure I have these permissions:\n"
            "✅ Ban Members\n"
            "✅ Manage Messages\n"
            "✅ View Channels\n"
            "✅ Send Messages\n"
            "✅ Read Message History\n\n"
            "Once set up, I'll automatically moderate scam messages and protect your group!"
        )

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Handle @SusMessageBot mentions as reports
    if client.user in message.mentions and message.reference:
        reported_msg = await message.channel.fetch_message(message.reference.message_id)
        is_admin = message.author.guild_permissions.administrator

        if is_admin:
            text = reported_msg.content or "[image]"
            add_example(text, "BAN")
            sync_example_to_github(text, "BAN")
            increment_stat('false_negatives')
            try:
                await reported_msg.delete()
                await reported_msg.author.ban(reason="Reported by admin")
                await message.channel.send("✅ User banned.")
            except Exception as e:
                logging.error(f"Error banning reported user: {e}")
        else:
            text = reported_msg.content or "[image]"
            view = ReportReviewView(
                user_id=reported_msg.author.id,
                username=str(reported_msg.author),
                text=text,
                message_id=reported_msg.id,
                channel_id=reported_msg.channel.id
            )
            await message.channel.send(
                f"🚨 Scam report by {message.author.mention}\n\n"
                f"👤 Reported user: {reported_msg.author} (`{reported_msg.author.id}`)\n"
                f"📝 Content: {text[:200]}",
                view=view
            )
        return

    if message.author.guild_permissions.administrator:
        return

    # Image moderation
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                loop = asyncio.get_event_loop()
                image_bytes = await attachment.read()
                result = await loop.run_in_executor(None, classify_image, bytes(image_bytes))
                if result == "BAN":
                    await _ban_user(message, reason="Suspicious image")
                    return

    if not message.content:
        return

    # Text + URL classification
    text = message.content
    loop = asyncio.get_event_loop()
    text_result = await loop.run_in_executor(None, classify_message, text)
    url_result = await loop.run_in_executor(None, analyze_urls, text)
    result = "BAN" if text_result == "BAN" or url_result == "BAN" else "SAFE"

    if result == "BAN":
        await _ban_user(message, reason="Suspicious message")
    else:
        increment_stat('messages_safe')


async def _ban_user(message: discord.Message, reason: str):
    """Delete message, ban user, notify admins with HITL buttons."""
    increment_stat('messages_ban')
    logging.info(f"BAN action taken on user {message.author.id}")

    try:
        await message.delete()
        await message.author.ban(reason=reason)

        view = HITLView(
            user_id=message.author.id,
            username=str(message.author),
            text=message.content[:200] if message.content else "[image]"
        )
        await message.channel.send(
            f"⚠️ Suspicious content detected and removed.\n\n"
            f"👤 User: {message.author} (`{message.author.id}`)\n\n"
            f"📝 Content: {message.content[:200] if message.content else '[image]'}"
            f"{'...' if message.content and len(message.content) > 200 else ''}",
            view=view
        )
    except Exception as e:
        logging.error(f"Error banning user: {e}")


class HITLView(discord.ui.View):
    def __init__(self, user_id: int, username: str, text: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.username = username
        self.text = text

    @discord.ui.button(label="✅ Correct Ban", style=discord.ButtonStyle.green)
    async def correct_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can do this.", ephemeral=True)
            return
        add_example(self.text, "BAN")
        sync_example_to_github(self.text, "BAN")
        increment_stat('bans_confirmed')
        await interaction.response.edit_message(content="✅ Ban confirmed.", view=None)

    @discord.ui.button(label="❌ Wrong Ban", style=discord.ButtonStyle.red)
    async def wrong_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can do this.", ephemeral=True)
            return
        add_example(self.text, "SAFE")
        sync_example_to_github(self.text, "SAFE")
        increment_stat('false_positives')
        try:
            await interaction.guild.unban(discord.Object(id=self.user_id))
        except Exception as e:
            logging.error(f"Error unbanning: {e}")
        await interaction.response.edit_message(content="❌ False positive confirmed. User unbanned.", view=None)


@client.tree.context_menu(name="Report to SusMessageBot")
async def report_context_menu(interaction: discord.Interaction, message: discord.Message):
    await _handle_report(interaction, message)


async def _handle_report(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=True)
    is_admin = interaction.user.guild_permissions.administrator

    if is_admin:
        text = message.content or "[image]"
        add_example(text, "BAN")
        sync_example_to_github(text, "BAN")
        increment_stat('false_negatives')
        try:
            await message.delete()
            await message.author.ban(reason="Reported by admin")
            await interaction.followup.send("✅ User banned.", ephemeral=True)
        except Exception as e:
            logging.error(f"Error banning reported user: {e}")
            await interaction.followup.send("✅ Added to training examples. Could not ban user.", ephemeral=True)
    else:
        text = message.content or "[image]"
        view = ReportReviewView(
            user_id=message.author.id,
            username=str(message.author),
            text=text,
            message_id=message.id,
            channel_id=message.channel.id
        )
        await interaction.followup.send(
            f"🚨 Scam report by {interaction.user.mention}\n\n"
            f"👤 Reported user: {message.author} (`{message.author.id}`)\n"
            f"📝 Content: {text[:200]}",
            view=view
        )


class ReportReviewView(discord.ui.View):
    def __init__(self, user_id: int, username: str, text: str, message_id: int, channel_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.username = username
        self.text = text
        self.message_id = message_id
        self.channel_id = channel_id

    @discord.ui.button(label="✅ Confirm Ban", style=discord.ButtonStyle.green)
    async def confirm_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can do this.", ephemeral=True)
            return
        add_example(self.text, "BAN")
        sync_example_to_github(self.text, "BAN")
        increment_stat('false_negatives')
        try:
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                msg = await channel.fetch_message(self.message_id)
                await msg.delete()
            await interaction.guild.ban(discord.Object(id=self.user_id), reason="Confirmed by admin")
            await interaction.response.edit_message(content="✅ Report confirmed. User banned.", view=None)
        except Exception as e:
            logging.error(f"Error banning reported user: {e}")
            await interaction.response.edit_message(content="✅ Could not ban user — they may have already left.", view=None)

    @discord.ui.button(label="❌ Dismiss", style=discord.ButtonStyle.red)
    async def dismiss(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can do this.", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ Report dismissed.", view=None)


def main():
    init_db()
    client.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()