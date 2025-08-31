import discord
from discord.ext import commands
from dm_handler import DMHandler
from dotenv import load_dotenv
import os
load_dotenv()


# --- CONFIG ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
CHANNEL_ID = 1411764328390066340

# --- DISCORD CLIENT SETUP ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
dm_handler = DMHandler(bot)

# --- UI Button View ---
class IntroduceButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Introduce me", style=discord.ButtonStyle.primary, custom_id="introduce_me")
    async def introduce_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        await interaction.response.send_message("Starting a private chat...", ephemeral=True)
        await dm_handler.start_dm_conversation(user)

# --- on_ready (optional static message at startup) ---
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        view = IntroduceButton()
        await channel.send("Would you like to be introduced to people?", view=view)
    else:
        print("❌ Could not find the channel.")

# --- DMs + command routing ---
@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return

    if isinstance(message.channel, discord.DMChannel):
        await dm_handler.handle_dm_message(message)

    await bot.process_commands(message)

# ✅ --- YOUR CUSTOM COMMAND ---
@bot.command(name="start")
async def start_intro(ctx):
    """Starts the intro process in any channel with a button."""
    view = IntroduceButton()
    await ctx.send("Would you like to be introduced to people?", view=view)

# --- RUN BOT ---
bot.run(DISCORD_TOKEN)