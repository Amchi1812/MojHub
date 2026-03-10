import load_env
# auth_gsheets.py
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# scopes koje trebamo
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']

def main():
    flow = InstalledAppFlow.from_client_secrets_file('oauth_credentials.json', SCOPES)
    # Otvara browser i traži autorizaciju; nakon prijave sprema creds
    creds = flow.run_local_server(port=0)  # otvara lokalni server i browser
    # spremi token za kasniju upotrebu
    with open('token.json', 'w') as f:
        f.write(creds.to_json())
    print("Got token.json — premjesti 'token.json' i 'oauth_credentials.json' na server gdje ćeš pokrenuti bota.")

if __name__ == '__main__':
    main()
