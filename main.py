import sys
sys.stdout.reconfigure(encoding="utf-8")

from gmail_client import get_unread_emails, get_gmail_service
from ai import analyze_email, generate_draft_reply
from parser import parse_response
from actions import handle_email
from sheets_client import append_email_row


def build_email_text(email):
    return f"""
Subject: {email.get('subject', '')}
From: {email.get('from', '')}

{email.get('body', '')}
""".strip()


def log_email(email, decision):
    if not decision:
        return False

    append_email_row(
        subject=email.get("subject", ""),
        sender=email.get("from", ""),
        summary=decision.get("summary", ""),
        priority=decision.get("priority", ""),
        action=decision.get("action", ""),
        is_important=decision.get("is_important", False),
    )
    return True


def apply_test_override(email, decision):
    # Disabled: this override caused false positives (for example test forwards).
    return decision


def precheck_forward_email(email):
    subject = (email.get("subject") or "").strip().lower()
    sender = (email.get("from") or "").strip().lower()
    body = (email.get("body") or "").strip().lower()

    # Deterministic ignore for automated/system traffic.
    if "no-reply" in sender or "automatic reply" in subject:
        print(f"Skipping auto/system email: {email.get('subject', '')}")
        return {
            "action": "ignore",
            "priority": "low",
            "is_important": False,
            "summary": "Automatic or system email",
        }

    # Deterministic ignore for forwarded emails without an explicit question.
    if (subject.startswith("fwd:") or subject.startswith("fw:")) and "?" not in body:
        print(f"Skipping forward email without clear request: {email.get('subject', '')}")
        return {
            "action": "ignore",
            "priority": "low",
            "is_important": False,
            "summary": "Forwarded email without clear customer request",
        }

    return None


def main():
    # Verify TO_REVIEW label exists before proceeding
    try:
        service = get_gmail_service()
        labels = service.users().labels().list(userId="me").execute()
        label_names = [label["name"] for label in labels.get("labels", [])]
        
        if "TO_REVIEW" not in label_names:
            print("⚠️ TO_REVIEW label does not exist. Skipping pipeline to avoid chaos.")
            raise SystemExit(1)
    except Exception as e:
        print(f"Error checking labels: {e}")
        raise SystemExit(1)
    
    emails = get_unread_emails(max_results=25)

    if not emails:
        print("No unread emails found.")
        raise SystemExit(0)

    for email in emails:
        try:
            print("\nProcessing:", email.get("subject", "(No subject)"))

            prechecked_decision = precheck_forward_email(email)
            if prechecked_decision:
                handle_email(email, prechecked_decision)
                try:
                    if log_email(email, prechecked_decision):
                        print("✅ Email logged to Google Sheets")
                except Exception as sheet_error:
                    print(f"⚠️ Skipping Sheets log due to error: {sheet_error}")
                continue

            email_text = build_email_text(email)

            print("DEBUG starting AI analysis")
            response_text = analyze_email(email_text)
            print("DEBUG AI response received:", bool(response_text))

            if not response_text or not response_text.strip():
                print("[analyze_email] Empty or invalid output. Skipping email.")
                continue

            print("DEBUG raw AI response:", response_text)

            decision = parse_response(response_text)
            print("DEBUG parsed response:", decision)

            if not decision:
                print("Parsing failed, skipping email without marking as read.")
                continue

            decision = apply_test_override(email, decision)

            if decision.get("action") == "reply":
                decision["draft_reply"] = generate_draft_reply(email)
                print("DRAFT REPLY:")
                print(decision["draft_reply"])

            handle_email(email, decision)

            try:
                if log_email(email, decision):
                    print("✅ Email logged to Google Sheets")
            except Exception as sheet_error:
                print(f"⚠️ Skipping Sheets log due to error: {sheet_error}")

            # Temporary debug mode: keep emails unread during testing.
            # mark_email_as_read(email["id"])
            # print("✅ Email marked as read")

        except Exception as e:
            print(f"Error processing email: {e}")
            continue


if __name__ == "__main__":
    main()
