from ai import analyze_email
from parser import parse_response

test_emails = [
    {
        "name": "Marketing",
        "content": """
Subject: 50% OFF SALE!!!
From: promo@shop.com

Huge discounts on all items. Click now!
""",
    },
    {
        "name": "Normal",
        "content": """
Subject: Meeting tomorrow
From: colleague@company.com

Hey, can we reschedule our meeting to 10am?
""",
    },
    {
        "name": "Important",
        "content": """
Subject: Damaged product received
From: client@business.com

Hello, I received the TV but it arrived broken. I need a replacement urgently.
""",
    },
]

for email in test_emails:
    print("\n========================")
    print("TEST:", email["name"])
    print("========================")

    response = analyze_email(email["content"])
    print("RAW AI OUTPUT:\n", response)

    parsed = parse_response(response)

    if parsed:
        print("PARSED OK:", parsed)
    else:
        print("FAILED TO PARSE")