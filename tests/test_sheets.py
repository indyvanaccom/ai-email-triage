import sheets_client
print("SHEETS_CLIENT FILE:", sheets_client.__file__)

from sheets_client import append_email_row

append_email_row(
    subject="TEST",
    sender="me",
    summary="it works",
    priority="high",
    action="reply_or_escalate",
    is_important=True,
)

print("DONE")