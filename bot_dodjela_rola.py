import load_env
import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ID kanala koji ćeš naknadno poslati
ROLE_CHANNEL_ID = int(os.getenv("ROLE_CHANNEL_ID", 0))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") 


# Mape za pitanja i emojije
role_messages = {
    "Dob": {
        "10–14": "1️⃣",
        "15–18": "2️⃣",
        "18–20": "3️⃣",
        "20+": "4️⃣"
    },
    "Spol": {
        "Muško": "🔵",
        "Žensko": "🟣"
    },
    "Status": {
        "Učenik": "👨‍🎓",
        "Student": "🎓",
        "Uposlenik MojHub": "🧑‍💼",
        "Volonter": "🙋",
        "Predavač/Mentor": "🧑‍🏫"
    },
    "Država": {
        "Bosna i Hercegovina": "🇧🇦",
        "Hrvatska": "🇭🇷",
        "Srbija": "🇷🇸",
        "Dijaspora/Ostalo": "🌍"
    }
}

# Čuvamo poruke da ih kasnije koristimo za reakcije
sent_messages = {}

@bot.event
async def on_ready():
    print(f"Bot {bot.user} je online")
    channel = bot.get_channel(ROLE_CHANNEL_ID)

    for category, options in role_messages.items():
        description = "\n".join([f"{emoji} = {role}" for role, emoji in options.items()])
        msg = await channel.send(f"**{category}**\n{description}")
        sent_messages[msg.id] = options

        # Dodaj reakcije
        for emoji in options.values():
            await msg.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    if payload.message_id in sent_messages:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        # pronadji koja rola odgovara ovom emojiju
        options = sent_messages[payload.message_id]
        for role_name, role_emoji in options.items():
            if emoji == role_emoji:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await member.add_roles(role)
                    print(f"Dodana rola {role_name} korisniku {member}")
                break

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return

    if payload.message_id in sent_messages:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        options = sent_messages[payload.message_id]
        for role_name, role_emoji in options.items():
            if emoji == role_emoji:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await member.remove_roles(role)
                    print(f"Uklonjena rola {role_name} korisniku {member}")
                break

bot.run(DISCORD_TOKEN)
