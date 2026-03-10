import load_env
import os.path
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# scopeovi
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ID tvog sheeta (uzmeš iz URL-a Google Sheeta)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

def init_gsheets():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("❌ Nema važećeg token.json — pokreni auth_gsheets.py prvo!")

    client = gspread.authorize(creds)
    return client

def append_to_sheet(row_data):
    """
    row_data = lista vrijednosti, npr:
    ["Ime Prezime", "Grad", "Datum rođenja", "Kontakt", "Interesovanja", "Discord Username", "Status"]
    """
    client = init_gsheets()
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    sheet.append_row(row_data)
    print("✅ Podaci upisani u Google Sheets:", row_data)

def read_sheet():
    """
    Čita sve redove iz Google Sheeta i vraća listu listi.
    """
    client = init_gsheets()
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    data = sheet.get_all_values()
    return data

