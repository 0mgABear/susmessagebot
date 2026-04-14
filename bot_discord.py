import discord
from discord.ext import commands
from moderator import classify_message
from image_moderator import classify_image
from url_moderator import analyze_urls, load_blocklist
from stats import init_db, get_stat, increment_stat, get_groups_count, get_total_members
from config import DISCORD_BOT_TOKEN
import logging
import asyncio

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    load_blocklist()
    logging.info(f"Bot ready — logged in as {bot.user}")
    for guild in bot.guilds:
        logging.info(f"Connected to server: {guild.name} ({guild.id})")

@bot.event
async def on_message(message: discord.Message):
    logging.info(f"Message received from {message.author}: {message.content}")
    logging.info(f"Attachments: {message.attachments}")
    if message.author.bot:
        return

    # Skip if author is admin/mod
    if message.author.guild_permissions.administrator:
        return

    text = message.content

    # Image moderation
    if message.attachments:
      for attachment in message.attachments:
          if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
              logging.info(f"Processing image: {attachment.filename}") 
              image_bytes = await attachment.read()
              logging.info(f"Image downloaded, size: {len(image_bytes)} bytes")
              loop = asyncio.get_event_loop()
              result = await loop.run_in_executor(None, classify_image, bytes(image_bytes))
              if result == "BAN":
                  await _ban_user(message, reason="Suspicious image")
                  return

    if not text:
        return

    # Text + URL classification
    text_result = classify_message(text)
    url_result = analyze_urls(text)
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

        # Send HITL notification with buttons
        view = HITLView(
            user_id=message.author.id,
            username=str(message.author),
            text=message.content[:200]
        )
        await message.channel.send(
            f"⚠️ Suspicious content detected and removed.\n\n"
            f"👤 User: {message.author} (`{message.author.id}`)\n\n"
            f"📝 Content: {message.content[:200]}{'...' if len(message.content) > 200 else ''}",
            view=view
        )
    except Exception as e:
        logging.error(f"Error banning user: {e}")


class HITLView(discord.ui.View):
    """HITL inline buttons for admin review."""

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
        from vector_store import add_example
        from github_sync import sync_example_to_github
        add_example(self.text, "BAN")
        sync_example_to_github(self.text, "BAN")
        increment_stat('bans_confirmed')
        await interaction.response.edit_message(content="✅ Ban confirmed.", view=None)

    @discord.ui.button(label="❌ Wrong Ban", style=discord.ButtonStyle.red)
    async def wrong_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can do this.", ephemeral=True)
            return
        from vector_store import add_example
        from github_sync import sync_example_to_github
        add_example(self.text, "SAFE")
        sync_example_to_github(self.text, "SAFE")
        increment_stat('false_positives')
        # Unban
        try:
            await interaction.guild.unban(discord.Object(id=self.user_id))
        except Exception as e:
            logging.error(f"Error unbanning: {e}")
        await interaction.response.edit_message(content="❌ False positive confirmed. User unbanned.", view=None)


def main():
    init_db()
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()