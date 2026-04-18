from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
)

print("client_email:", creds.service_account_email)
print("project_id:", creds.project_id)
print("ok")
