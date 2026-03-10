import load_env
import discord
from discord.ext import tasks, commands
import requests
from datetime import datetime, timedelta, time as dtime  # time je već u discordu, pa koristimo alias
import os
# === KONFIGURACIJA ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # tvoj bot token
KALENDAR_CHANNEL_ID = int(os.getenv("KALENDAR_CHANNEL_ID", 0))
WP_API_URL = "https://mojhub.ba/?rest_route=/wp/v2/obuke"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} je online!")
    provjeri_obuke.start()  # pokreće task

# === TASK: provjera obuka ===
@tasks.loop(time=dtime(hour=9, minute=0))  # svaki dan u 09:00
async def provjeri_obuke():
    try:
        response = requests.get(WP_API_URL)
        response.raise_for_status()
        obuke = response.json()
    except Exception as e:
        print("Greška pri dohvaćanju obuka:", e)
        return

    sutra = datetime.now().date() + timedelta(days=1)
    kanal = bot.get_channel(KALENDAR_CHANNEL_ID)
    if not kanal:
        print("Kanal nije pronađen!")
        return

    for obuka in obuke:
        acf = obuka.get("acf", {})
        datum_str = acf.get("datum_pocetka")
        if not datum_str:
            continue

        # Parsiranje datuma iz formata YYYYMMDD
        try:
            datum_pocetka = datetime.strptime(datum_str, "%Y%m%d").date()
        except ValueError:
            print(f"Neispravan datum za obuku {obuka['title']['rendered']}")
            continue

        # Ako obuka počinje sutra
        if datum_pocetka == sutra:
            naziv = obuka["title"]["rendered"]
            link = obuka["link"]
            poruka = f"📌 Obuka **{naziv}** počinje sutra ({datum_pocetka.strftime('%d.%m.%Y')})! Više info: {link}"
            await kanal.send(poruka)

# === POKRETANJE BOTA ===
bot.run(DISCORD_TOKEN)

