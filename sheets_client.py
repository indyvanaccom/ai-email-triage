print("USING CURRENT SHEETS_CLIENT")
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = "1pBjKrRlpupE0cy7nscXEIHD6VwC35GT3beIW-bZTe-8"


def get_worksheet():
    credentials = Credentials.from_service_account_file(
        "config/service_account.json",
        scopes=SCOPES,
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.sheet1
    return worksheet


def append_email_row(subject, sender, summary, priority, action, is_important):
    worksheet = get_worksheet()
    processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    worksheet.append_row([
        processed_at,
        subject,
        sender,
        summary,
        priority,
        action,
        str(is_important),
    ])