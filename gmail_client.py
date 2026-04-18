import base64
import os
from email import message_from_bytes
from email.message import EmailMessage
from email.utils import parseaddr

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service():
    creds = None

    if os.path.exists("config/token.json"):
        creds = Credentials.from_authorized_user_file("config/token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "config/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("config/token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def extract_plain_text_from_payload(payload: dict) -> str:
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    data = body.get("data")

    if mime_type == "text/plain" and data:
        decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
        return decoded.decode("utf-8", errors="ignore")

    if mime_type == "text/html" and data:
        decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
        html = decoded.decode("utf-8", errors="ignore")
        return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)

    for part in payload.get("parts", []) or []:
        text = extract_plain_text_from_payload(part)
        if text:
            return text

    return ""


def get_latest_unread_email():
    service = get_gmail_service()

    results = (
        service.users()
        .messages()
        .list(userId="me", q="is:unread", maxResults=1)
        .execute()
    )

    messages = results.get("messages", [])
    if not messages:
        return None

    msg_id = messages[0]["id"]

    msg = (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="full")
        .execute()
    )

    headers = msg["payload"].get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "")

    body = extract_plain_text_from_payload(msg["payload"])

    return {
        "id": msg_id,
        "subject": subject,
        "from": sender,
        "body": body,
    }


def get_unread_emails(max_results=10):
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"],
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = msg_data["payload"]["headers"]

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")

        body = extract_plain_text_from_payload(msg_data["payload"])

        emails.append({
            "id": msg["id"],
            "thread_id": msg_data.get("threadId"),
            "subject": subject,
            "from": sender,
            "body": body
        })

    return emails


def mark_email_as_read(message_id):
    try:
        print("DEBUG mark_email_as_read called with:", message_id)

        service = get_gmail_service()

        result = service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

        print("DEBUG mark_email_as_read succeeded:", result)
        return result

    except Exception as e:
        print("DEBUG mark_email_as_read failed:", repr(e))
        raise


def archive_email(message_id):
    try:
        service = get_gmail_service()
        return service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["INBOX"]}
        ).execute()
    except Exception as e:
        print("DEBUG archive_email failed:", repr(e))
        raise


def create_draft(email_data, draft_text):
    service = get_gmail_service()

    sender_header = email_data.get("from", "")
    _, sender_email = parseaddr(sender_header)
    to_value = sender_email or sender_header

    subject = email_data.get("subject", "")
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    message = EmailMessage()
    if to_value:
        message["To"] = to_value
    if subject:
        message["Subject"] = subject
    message.set_content(draft_text)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft_body = {"message": {"raw": raw}}

    thread_id = email_data.get("thread_id")
    if thread_id:
        draft_body["message"]["threadId"] = thread_id

    return service.users().drafts().create(userId="me", body=draft_body).execute()


def add_label(message_id, label_name):
    service = get_gmail_service()

    # get existing labels
    labels = service.users().labels().list(userId="me").execute()
    label_id = None

    for label in labels["labels"]:
        if label["name"] == label_name:
            label_id = label["id"]
            break

    # create label if not exists
    if not label_id:
        label = service.users().labels().create(
            userId="me",
            body={"name": label_name}
        ).execute()
        label_id = label["id"]

    # apply label
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id]}
    ).execute()


def get_thread_sent_messages(thread_id):
    service = get_gmail_service()
    # Query for messages we sent in this thread
    results = service.users().messages().list(
        userId="me",
        q=f"threadId:{thread_id} from:me"
    ).execute()
    return results.get("messages", [])


def clean_thread_sent_messages(thread_id):
    service = get_gmail_service()
    sent_messages = get_thread_sent_messages(thread_id)
    for msg in sent_messages:
        try:
            service.users().messages().trash(
                userId="me",
                id=msg["id"]
            ).execute()
        except Exception as e:
            print(f"Error trashing message: {e}")