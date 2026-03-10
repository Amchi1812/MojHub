import load_env
import discord
from discord.ext import commands
import re
import os

  # ⚠️ nemoj javno dijeliti pravi token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_MAP = {
    "IT": int(os.getenv("CHANNEL_IT_ID")),
    "Jezici": int(os.getenv("CHANNEL_JEZICI_ID")),
    "Psihologija": int(os.getenv("CHANNEL_PSIHOLOGIJA_ID")),
    "Šerijat": int(os.getenv("CHANNEL_SERIJAT_ID")),
    "Ekonomija": int(os.getenv("CHANNEL_EKONOMIJA_ID")),
    "Sport": int(os.getenv("CHANNEL_SPORT_ID")),
}

CATEGORY_MAP = {
    "IT": int(os.getenv("CATEGORY_IT_ID")),
    "Jezici": int(os.getenv("CATEGORY_JEZICI_ID")),
    "Psihologija": int(os.getenv("CATEGORY_PSIHOLOGIJA_ID")),
    "Šerijat": int(os.getenv("CATEGORY_SERIJAT_ID")),
    "Ekonomija": int(os.getenv("CATEGORY_EKONOMIJA_ID")),
    "Sport": int(os.getenv("CATEGORY_SPORT_ID")),
}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ popravljena funkcija za ime kanala
def format_channel_name(naslov: str) -> str:
    naslov = naslov.lower()
    naslov = re.sub(r'[^a-z0-9]+', '-', naslov)   # zamijeni sve što nije slovo ili broj sa "-"
    naslov = re.sub(r'-+', '-', naslov)           # višestruke crtice → jedna
    naslov = naslov.strip('-')                    # ukloni crtice na početku i kraju
    return f"obuka-{naslov}"

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} je online")

async def handle_obuka_message(message: discord.Message, oblast: str):
    guild = message.guild

    naslov = None

    # Embed verzija
    if message.embeds:
        embed = message.embeds[0]
        if embed.title:
            naslov = embed.title.strip()
        elif embed.description:
            naslov = embed.description.splitlines()[0].strip()

    # Tekstualna poruka
    if not naslov and message.content.strip():
        naslov = message.content.splitlines()[0].strip()

    if not naslov:
        print("⚠️ Nije pronađen naslov ni u poruci ni u embed-u.")
        return

    print(f"📌 Naslov obuke: {naslov}")

    role_name = f"Obuka {naslov}"
    channel_name = format_channel_name(naslov)
    voice_name = f"{channel_name}-voice"

    # ROLE
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        role = await guild.create_role(name=role_name)
        print(f"🟢 Kreirana rola: {role_name}")
    else:
        print(f"ℹ️ Rola već postoji: {role_name}")

    # CATEGORY
    category = discord.utils.get(guild.categories, id=CATEGORY_MAP[oblast])

    # TEKSTUALNI (provjera unutar kategorije da ne duplira)
    text_channel = None
    for ch in category.text_channels:
        if ch.name.strip().lower() == channel_name.strip().lower():
            text_channel = ch
            break

    if not text_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        print(f"🟢 Kreiran tekstualni kanal: {channel_name}")
    else:
        print(f"ℹ️ Tekstualni kanal već postoji: {text_channel.name} (ID: {text_channel.id})")

    # VOICE
    voice_channel = discord.utils.get(guild.voice_channels, name=voice_name)
    if not voice_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
            role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, stream=True)
        }
        await guild.create_voice_channel(voice_name, category=category, overwrites=overwrites)
        print(f"🟢 Kreiran voice kanal: {voice_name}")
    else:
        print(f"ℹ️ Voice kanal već postoji: {voice_name}")

@bot.event
async def on_message(message):
    # ⚠️ maknuto: if message.author == bot.user: return
    # jer obuke šalje bot embed-om

    for oblast, kanal_id in CHANNEL_MAP.items():
        if message.channel.id == kanal_id:
            await handle_obuka_message(message, oblast)
            break

    await bot.process_commands(message)

# ako embed bude dodan editom (često kod webhooka / integracija)
@bot.event
async def on_message_edit(before, after):
    for oblast, kanal_id in CHANNEL_MAP.items():
        if after.channel.id == kanal_id:
            await handle_obuka_message(after, oblast)
            break

bot.run(DISCORD_TOKEN)


