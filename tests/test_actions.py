from actions import handle_email

fake_email = {
    "subject": "Meeting tomorrow",
    "from": "colleague@company.com"
}

parsed = {
    "is_important": True,
    "priority": "medium",
    "summary": "Colleague wants to reschedule a meeting.",
    "action": "log_only"
}

print("TEST EMAIL:", fake_email)
handle_email(parsed)
