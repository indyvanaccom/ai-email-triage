from sheets_client import append_email_row
from gmail_client import create_draft, add_label, archive_email, clean_thread_sent_messages


def log_important_email(email, parsed):
    if not parsed:
        return False

    action = parsed.get("action")

    if action not in {"log_only", "notify", "draft_reply"}:
        return False

    append_email_row(
        subject=email.get("subject", ""),
        sender=email.get("from", ""),
        summary=parsed.get("summary", ""),
        priority=parsed.get("priority", ""),
        action=parsed.get("action", ""),
    )
    return True


def handle_email(email, decision):
    action = decision.get("action")

    if action == "reply":
        draft = decision.get("draft_reply", "").strip()

        if not draft or len(draft) < 20:
            print("Invalid draft, skipping:", email["subject"])
            return

        create_draft(email, draft)
        add_label(email["id"], "TO_REVIEW")
        clean_thread_sent_messages(email.get("thread_id"))
        archive_email(email["id"])

        print("Reply → draft + TO_REVIEW + archive:", email["subject"])

    elif action == "escalate":
        add_label(email["id"], "URGENT")
        # bewust NIET markeren als gelezen

        print("Escalate → URGENT (unread):", email["subject"])

    elif action == "ignore":
        clean_thread_sent_messages(email.get("thread_id"))
        archive_email(email["id"])

        print("Ignore → archive:", email["subject"])