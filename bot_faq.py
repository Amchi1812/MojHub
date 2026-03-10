import load_env
import discord
from discord.ext import commands
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # već uključen
bot = commands.Bot(command_prefix="!", intents=intents)

faq = {
    "Kako da se pridružim MojHub-u?": "Da biste se pridružili MojHub-u, kliknite na kanal #prijava i slijedite upute.",
    "Koji kursevi su dostupni?": "Trenutno nudimo kurseve iz IT-a, jezika, psihologije, ekonomije i šerijata.",
    "Kako da dobijem pristup kursevima?": "Pristup kursevima se dobija nakon što odaberete svoje interesovanje kroz naš sistem anketa.",
    "Kako da kontaktiram podršku?": "Možete nam poslati DM ili koristiti kanal #podrska za pitanja.",
    "Da li se kursevi održavaju online ili uživo?": "Većina kurseva se održava online, dok će se neke specijalne radionice održavati uživo uz prethodnu najavu.",
    "Koje su cijene kurseva?": "Cijene kurseva variraju, a detalje o svakoj obuci možete pronaći u opisu obuke na kanalu #obuke.",
    "Kako da se odjavim sa kursa?": "Za odjavu sa kursa, kontaktirajte nas putem kanala #podrska najmanje 24h prije početka kursa.",
    "Mogu li preporučiti kurs prijatelju?": "Naravno! Možete dijeliti linkove kurseva ili ga uputiti da se prijavi kroz kanal #prijava.",
    "Kako da predložim novo interesovanje ili kurs?": "Pošaljite prijedlog kroz kanal #prijedlozi ili direktno administratoru bota.",
    "Da li MojHub izdaje certifikate?": "Da, za završene kurseve izdaju se digitalni certifikati koji se mogu preuzeti nakon završetka kursa.",
    "Kako da pratim nove obuke i vijesti?": "Najbolje je da pratite kanal #obuka-info gdje se automatski objavljuju sve nove obuke i novosti.",
}


class FAQButton(discord.ui.Button):
    def __init__(self, pitanje, odgovor):
        super().__init__(label=pitanje, style=discord.ButtonStyle.primary)
        self.odgovor = odgovor

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.odgovor, ephemeral=True)

class FAQView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for pitanje, odgovor in faq.items():
            self.add_item(FAQButton(pitanje, odgovor))

FAQ_CHANNEL_ID = int(os.getenv("FAQ_CHANNEL_ID", 0)) # tvoj kanal ❓│pitanja-i-odgovori

@bot.event
async def on_ready():
    print(f"{bot.user} je online!")
    channel = bot.get_channel(FAQ_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="❓ Najčešća pitanja o MojHub-u",
            description="Kliknite dugme ispod pitanja da dobijete odgovor (samo vi ćete ga vidjeti).",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=FAQView())
    else:
        print("Kanal nije pronađen. Provjeri CHANNEL_ID!")

bot.run(DISCORD_TOKEN)

