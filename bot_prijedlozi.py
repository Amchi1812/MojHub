import load_env
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from datetime import datetime
import os
import json

# ===================== KONFIGURACIJA =====================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PRIJEDLOZI_CHANNEL_ID = int(os.getenv("PRIJEDLOZI_CHANNEL_ID", 0))  # Kanal 🤝│prijedlozi

# Google Sheets
SHEET_ID = os.getenv("SHEET_ID")
OAUTH_CREDENTIALS_FILE = "oauth_credentials.json"
TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ===================== GOOGLE SHEETS AUTENTIKACIJA =====================
creds = None

# Ako postoji spremljeni token, učitaj ga
if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
else:
    # Ako nema tokena, pokreni OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    # Spremi token u token.json
    with open(TOKEN_FILE, "w") as token_file:
        token_file.write(creds.to_json())

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).worksheet("Prijedlozi")

# ===================== DISCORD BOT =====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== MODAL =====================
class SuggestionModal(Modal):
    def __init__(self):
        super().__init__(title="Pošalji prijedlog")
        self.add_item(
            TextInput(
                label="Unesi svoj prijedlog",
                style=discord.TextStyle.paragraph,
                placeholder="Ovdje napiši prijedlog..."
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        # Odmah pošalji ephemeral potvrdu korisniku
        await interaction.response.send_message("Hvala! Tvoj prijedlog je poslan.", ephemeral=True)

        user = interaction.user.name
        text = self.children[0].value
        vrijeme = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Pokušaj zapis u Google Sheets
        try:
            sheet.append_row([user, text, vrijeme])
        except Exception as e:
            print(f"Greška pri zapisivanju u Sheets: {e}")

# ===================== VIEW SA DUGMETOM =====================
class SuggestionView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Dugme stalno aktivno

        # Kreiraj dugme i callback
        button = Button(label="Pošalji prijedlog", style=discord.ButtonStyle.primary)

        async def button_callback(interaction: discord.Interaction):
            modal = SuggestionModal()
            await interaction.response.send_modal(modal)

        button.callback = button_callback
        self.add_item(button)

# ===================== ON_READY =====================
@bot.event
async def on_ready():
    print(f"{bot.user} je online!")

    channel = bot.get_channel(PRIJEDLOZI_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🤝 Pošalji prijedlog",
            description="Ako imate neki prijedlog, primijetili ste neku grešku ili slično, pritisnite dugme ispod.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed, view=SuggestionView())
    else:
        print("Kanal nije pronađen. Provjeri CHANNEL_ID!")

# ===================== POKRETANJE BOTA =====================
bot.run(DISCORD_TOKEN)



