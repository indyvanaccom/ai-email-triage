from sheets_client import append_email_row


append_email_row(
    subject="TEST SUBJECT",
    sender="test@example.com",
    summary="manual sheet test",
    priority="low",
    action="test",
    status="test"
)