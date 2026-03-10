import load_env
import os
import re  # ostavljam jer se koristi za datum, ali više ne za rolu
import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime

# === Google Sheets ===
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# === KONFIGURACIJA ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WP_API_URL = "https://mojhub.ba/?rest_route=/wp/v2/obuke"
SPREADSHEET_ID2 = os.getenv("SPREADSHEET_ID2")

CHANNEL_MAP = {
    "IT": int(os.getenv("CHANNEL_IT_ID")),
    "Jezici": int(os.getenv("CHANNEL_JEZICI_ID")),
    "Psihologija": int(os.getenv("CHANNEL_PSIHOLOGIJA_ID")),
    "Šerijat": int(os.getenv("CHANNEL_SERIJAT_ID")),
    "Ekonomija": int(os.getenv("CHANNEL_EKONOMIJA_ID")),
    "Sport": int(os.getenv("CHANNEL_SPORT_ID")),
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

posted_obuke = set()
processed_submissions = set()  # sprječava duple upise kod submit-a


# === GOOGLE SHEETS SERVICE ===
def get_gsheets_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("oauth_credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)


# === DISCORD UI KOMPONENTE ===
class PrijavaModal(discord.ui.Modal, title="Prijava na obuku"):
    def __init__(self, obuka_title, oblast):
        super().__init__()
        self.obuka_title = obuka_title
        self.oblast = oblast

        self.roditelj = discord.ui.TextInput(label="Ime i prezime roditelja", required=True)
        self.kontakt = discord.ui.TextInput(label="Kontakt roditelja", required=True)
        self.dijete = discord.ui.TextInput(label="Ime i prezime djeteta", required=True)

        self.add_item(self.roditelj)
        self.add_item(self.kontakt)
        self.add_item(self.dijete)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "✅ Tvoja prijava je zaprimljena, obrada u toku...", ephemeral=True
        )

        unique_key = f"{interaction.user.id}-{self.obuka_title}"
        if unique_key in processed_submissions:
            await interaction.followup.send(
                "⚠️ Već si poslao/la prijavu za ovu obuku.", ephemeral=True
            )
            return
        processed_submissions.add(unique_key)

        try:
            service = get_gsheets_service()
            sheet = service.spreadsheets()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [
                now,
                interaction.user.name,
                str(interaction.user.id),
                self.roditelj.value,
                self.kontakt.value,
                self.dijete.value,
                self.obuka_title,
            ]
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID2,
                range="Prijave!A:G",
                valueInputOption="RAW",
                body={"values": [row]},
            ).execute()

            await interaction.followup.send(
                "🎉 Prijava je uspješno zabilježena!", ephemeral=True
            )

            guild = interaction.guild
            if guild:
                # 🔑 Sada koristimo tačan naslov bez čišćenja
                role_name = f"Obuka {self.obuka_title}"
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await interaction.user.add_roles(role)
                    print(f"✅ Dodana rola '{role_name}' korisniku {interaction.user}")
                else:
                    print(f"⚠️ Rola '{role_name}' nije pronađena na serveru.")

        except Exception as e:
            await interaction.followup.send(
                f"⚠️ Greška pri prijavi: {e}", ephemeral=True
            )


class ObukaView(discord.ui.View):
    def __init__(self, link, title, oblast):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Saznaj više", url=link))
        self.add_item(PrijaviSeButton(title, oblast))


class PrijaviSeButton(discord.ui.Button):
    def __init__(self, obuka_title, oblast):
        super().__init__(label="Prijavi se", style=discord.ButtonStyle.success)
        self.obuka_title = obuka_title
        self.oblast = oblast

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PrijavaModal(self.obuka_title, self.oblast))


# === TASK: povlačenje obuka sa weba ===
@tasks.loop(minutes=1)
async def fetch_obuke():
    try:
        resp = requests.get(WP_API_URL, timeout=10)
        if resp.status_code != 200:
            print("❌ Greška API request")
            return

        for obuka in resp.json():
            obuka_id = obuka["id"]
            if obuka_id in posted_obuke:
                continue

            oblast = obuka["acf"].get("oblast")
            channel_id = CHANNEL_MAP.get(oblast)
            if not channel_id:
                print(f"⚠️ Nepoznata oblast: {oblast}")
                continue

            channel = bot.get_channel(channel_id)
            if not channel:
                print(f"⚠️ Kanal nije pronađen: {channel_id}")
                continue

            title = obuka["title"]["rendered"]
            opis = obuka["acf"].get("opis", "Nema opisa.")
            datum_raw = obuka["acf"].get("datum_pocetka", "Nepoznat datum")

            # Formatiranje datuma (YYYYMMDD ➜ DD.MM.YYYY)
            datum = "Nepoznat datum"
            if isinstance(datum_raw, str) and re.fullmatch(r"\d{8}", datum_raw):
                try:
                    d = datetime.strptime(datum_raw, "%Y%m%d")
                    datum = d.strftime("%d.%m.%Y.")
                except ValueError:
                    datum = datum_raw
            else:
                datum = datum_raw

            link = obuka.get("link", "https://mojhub.ba")

            embed = discord.Embed(title=title, description=opis, color=discord.Color.blue())
            embed.add_field(name="📅 Datum početka", value=datum, inline=False)

            featured_media = obuka.get("featured_media")
            if featured_media:
                media_resp = requests.get(
                    f"https://mojhub.ba/?rest_route=/wp/v2/media/{featured_media}", timeout=10
                )
                if media_resp.status_code == 200:
                    img_url = media_resp.json().get("source_url")
                    if img_url:
                        embed.set_image(url=img_url)

            await channel.send(embed=embed, view=ObukaView(link, title, oblast))
            posted_obuke.add(obuka_id)

    except Exception as e:
        print(f"⚠️ Greška u fetch_obuke: {e}")


@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} je online")
    fetch_obuke.start()


bot.run(DISCORD_TOKEN)






