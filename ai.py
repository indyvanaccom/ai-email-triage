from openai import OpenAI
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT_SECONDS = 20

client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY"),
  http_client=httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS),
)


def analyze_email(email_text, retries=2, delay=2):
  prompt = f"""
Analyze this email and return ONLY valid JSON.

Required JSON format:
{{
  "is_important": true or false,
  "priority": "low" or "medium" or "high",
  "summary": "short summary",
  "action": "ignore" or "reply" or "escalate"
}}

ACTION_RULES:

1. REPLY (default case):
- Any normal customer question
- Order status, delivery, invoice, account, product info
- Mild confusion or doubt (even if slightly negative tone)
- If in doubt between reply and escalate, choose "reply"

2. ESCALATE (only if clearly needed):
- Strong complaints or repeated frustration
- Legal threats, refund demands, chargebacks
- Payment issues or blocked access
- Angry or aggressive tone
- Only use "escalate" when human intervention is clearly required

3. IGNORE (strict filtering):
- Newsletters, promotions, marketing campaigns
- Automated emails (discounts, offers, subscriptions)
- No direct question or request from a customer
- Emails starting with "Fwd:" or "FW:" without a clear customer request
- Emails starting with "Fwd:" or "FW:" that do not contain a clear, direct customer request
- Forwarded emails without explicit question directed at support
- Automatic replies (out of office, delivery notifications)
- System emails or no-reply senders
- If sender looks like a brand, platform, or marketing domain, likely ignore unless a real customer question is present
- If the email does not contain a clear question or request -> ignore

NEWSLETTER DETECTION SIGNALS:
- Presence of discount-heavy promo language (for example: "-50%", "promotion", "offer")
- CTA like "click here", "discover", "shop now"
- If these are present and there is no real customer request, choose "ignore"

PRIORITY_RULES:
- If action == "ignore", priority MUST be "low"
- If action == "reply", priority MUST be "low" or "medium"
- If action == "escalate", priority MUST be "high"

IMPORTANCE_RULES:
- If action == "ignore", is_important MUST be false
- If action == "reply" or "escalate", is_important MUST be true

Rules:
- Return valid JSON only
- No markdown
- No explanation
- No text before or after JSON

Email:
{email_text}
"""

  for attempt in range(1, retries + 1):
    try:
      print(f"[analyze_email] Starting attempt {attempt}/{retries}")
      print("[analyze_email] Sending request to OpenAI")

      response = client.responses.create(
        model="gpt-5",
        input=prompt,
        timeout=REQUEST_TIMEOUT_SECONDS,
      )

      print(f"[analyze_email] Response object received on attempt {attempt}/{retries}")
      output_text = response.output_text.strip()
      print(f"[analyze_email] Response text length: {len(output_text)}")
      return output_text

    except Exception as e:
      print(f"[analyze_email] Attempt {attempt}/{retries} failed: {e}")

      if attempt < retries:
        print(f"[analyze_email] Sleeping {delay}s before retry")
        time.sleep(delay)

  print("[analyze_email] All attempts failed")
  return None


def generate_draft_reply(email, retries=2, delay=2):
  prompt = f"""
You are a professional customer support assistant.

Write a short, clear, polite email reply in the same language as the original email.

Guidelines for the reply:
- Be concise and proactive
- Ask only for the minimum necessary information
- Prefer one single clear question if a question is needed
- Remove unnecessary options or multiple questions
- Show ownership ("we will check", "I will verify")
- Use strong proactive phrasing when relevant (for example: "I will check immediately")
- Avoid generic openings like "Thank you for your message"
- Avoid generic phrases like "sorry for the inconvenience" unless clearly needed
- Keep a natural, human support-agent tone (not templated)
- Prefer 1 clear next step over multiple questions
- Use concrete timelines when relevant (for example: "today", "within 24h")
- Avoid vague timing words like "soon" or "rapidly"
- Always include one clear and concrete timeframe whenever possible

Greeting safety rules:
- Do not use the customer's name unless you are highly certain it is correct
- If writing in Dutch, default greeting: "Hoi,"
- If writing in French, default greeting: "Bonjour,"
- Otherwise, use a neutral greeting like "Hello,"

Subject: {email['subject']}
From: {email['from']}
Body:
{email['body']}

Return only the reply text, no intro, no explanation.
"""

  for attempt in range(1, retries + 1):
    try:
      print(f"[generate_draft_reply] Starting attempt {attempt}/{retries}")
      response = client.responses.create(
        model="gpt-5",
        input=prompt,
        timeout=REQUEST_TIMEOUT_SECONDS,
      )
      output_text = response.output_text.strip()
      print(f"[generate_draft_reply] Draft length: {len(output_text)}")
      return output_text
    except Exception as e:
      print(f"[generate_draft_reply] Attempt {attempt}/{retries} failed: {e}")
      if attempt < retries:
        print(f"[generate_draft_reply] Sleeping {delay}s before retry")
        time.sleep(delay)

  print("[generate_draft_reply] All attempts failed")
  return ""