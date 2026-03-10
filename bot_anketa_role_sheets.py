import load_env
import discord
from discord.ext import commands, tasks
from sheets_utils import append_to_sheet, read_sheet
import asyncio
import os


# === KONFIGURACIJA ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PRAVILA_CHANNEL_ID = int(os.getenv("PRAVILA_CHANNEL_ID", 0))

VERIFIED_ROLE_NAME = "Verified"

# === Status vrijednosti ===
STATUS_PENDING = "Na čekanju"
STATUS_APPROVED = "Odobreno"
STATUS_REJECTED = "Odbijeno"

# === Mapa interesovanja → role ===
INTEREST_ROLES = {
    "it": "it",
    "jezici": "jezici",
    "psihologija": "psihologija",
    "šerijat": "serijet",
    "serijat": "serijet",
    "ekonomija": "ekonomija",
    "sport": "sport"
}

# === INTENTS ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Set za praćenje DM poslanih odbijenim korisnicima ===
dm_sent_rejected = set()

# === MODAL ZA ANKETU ===
class SurveyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📋 MojHub Anketa", custom_id="survey_modal")
        self.add_item(discord.ui.TextInput(label="Ime i prezime", placeholder="Unesi svoje ime i prezime", required=True))
        self.add_item(discord.ui.TextInput(label="Grad", placeholder="Unesi grad iz kojeg dolaziš", required=True))
        self.add_item(discord.ui.TextInput(label="Datum rođenja", placeholder="DD.MM.GGGG", required=True))
        self.add_item(discord.ui.TextInput(label="Kontakt (E-mail i Telefon)", placeholder="primjer@mail.com, +387...", required=True))
        self.add_item(discord.ui.TextInput(
            label="Interesovanja",
            placeholder="Odaberi više (mala slova!): it, jezici, psihologija, šerijat, ekonomija, sport",
            style=discord.TextStyle.paragraph,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        row = [
            self.children[0].value,
            self.children[1].value,
            self.children[2].value,
            self.children[3].value,
            self.children[4].value,
            str(interaction.user),
            STATUS_PENDING
        ]
        gs_ok = False
        try:
            await asyncio.to_thread(append_to_sheet, row)
            gs_ok = True
            print(f"✅ Podaci upisani u Google Sheets za {interaction.user}")
        except Exception as e:
            print(f"⚠️ Greška pri upisu u Google Sheets: {e}")

        embed = discord.Embed(
            title="✅ Anketa popunjena",
            description="Tvoje informacije su zaprimljene i čekaju odobrenje administratora.",
            color=0xf1c40f
        )
        embed.add_field(name="Ime i prezime", value=self.children[0].value, inline=False)
        embed.add_field(name="Grad", value=self.children[1].value, inline=False)
        embed.add_field(name="Datum rođenja", value=self.children[2].value, inline=False)
        embed.add_field(name="Kontakt", value=self.children[3].value, inline=False)
        embed.add_field(name="Interesovanja", value=self.children[4].value, inline=False)
        embed.add_field(name="Status", value=STATUS_PENDING, inline=False)
        embed.add_field(name="Google Sheets", value="UPISANO" if gs_ok else "GREŠKA", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

# === VIEW ZA DUGME "Pokreni anketu" ===
class SurveyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="📋 Pokreni anketu", style=discord.ButtonStyle.primary, custom_id="start_survey")
    async def start_survey(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SurveyModal())

# === VIEW ZA PRAVILA ===
class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="✅ Prihvatam pravila", style=discord.ButtonStyle.success, custom_id="accept_rules")
    async def accept_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✅ Hvala što si prihvatio/la pravila!\nKlikni ispod da pokreneš anketu za verifikaciju:",
            view=SurveyView(),
            ephemeral=True
        )

# === TASK ZA PROVJERU GOOGLE SHEETS STATUSA ===
@tasks.loop(seconds=60)
async def check_sheet_status():
    print("🔄 Provjeravam statuse u Google Sheets...")
    try:
        data = await asyncio.to_thread(read_sheet)
    except Exception as e:
        print(f"⚠️ Greška pri čitanju Google Sheets: {e}")
        return
    if not data or len(data) < 2:
        return

    headers = data[0]
    for row in data[1:]:
        if len(row) < 7:
            continue
        ime, grad, datum, kontakt, interesovanja, discord_username, status = row
        guild = bot.guilds[0] if bot.guilds else None
        if not guild:
            return
        member = guild.get_member_named(discord_username)
        if not member:
            continue

        if status == STATUS_APPROVED:
            verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
            if verified_role and verified_role not in member.roles:
                try:
                    await member.add_roles(verified_role, reason="Anketa odobrena u Google Sheets")
                except Exception as e:
                    print(f"⚠️ Ne mogu dodati Verified rolu {member}: {e}")
            for key, role_name in INTEREST_ROLES.items():
                if key in interesovanja.lower():
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role and role not in member.roles:
                        try:
                            await member.add_roles(role, reason="Interest role via odobrena anketa")
                        except Exception as e:
                            print(f"⚠️ Ne mogu dodati rolu {role_name} za {member}: {e}")

        elif status == STATUS_REJECTED:
            if discord_username not in dm_sent_rejected:
                try:
                    await member.send("❌ Nažalost, tvoja anketa je odbijena od strane administratora.")
                    dm_sent_rejected.add(discord_username)
                except Exception:
                    print(f"⚠️ Ne mogu poslati DM korisniku {member}")

# === ON_READY ===
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} je pokrenut!")
    channel = bot.get_channel(PRAVILA_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="📜 Potvrdi da si pročitao pravila MojHub servera",
            description="Klikni na dugme ispod da potvrdiš da si pročitao/la pravila.",
            color=0x2ecc71
        )
        view = RulesView()
        await channel.send(embed=embed, view=view)
    check_sheet_status.start()

# === POKRETANJE BOTA ===
bot.run(DISCORD_TOKEN)
