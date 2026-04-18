import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = "1pBjKrRlpupE0cy7nscXEIHD6VwC35GT3beIW-bZTe-8"

credentials = Credentials.from_service_account_file(
    "service_account.json",
    scopes=SCOPES,
)

client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID)

print("TITLE:", sheet.title)
print("OK")