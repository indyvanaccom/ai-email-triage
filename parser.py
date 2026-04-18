import json

ALLOWED_PRIORITIES = {"low", "medium", "high"}
ALLOWED_ACTIONS = {"ignore", "reply", "escalate"}


def parse_response(response_text):
    try:
        if not response_text:
            raise ValueError("Empty response")

        data = json.loads(response_text)

        if not isinstance(data, dict):
            raise ValueError("Response must be a JSON object")

        required_keys = ["is_important", "priority", "summary", "action"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing key: {key}")

        if data["priority"] not in ALLOWED_PRIORITIES:
            raise ValueError("Invalid priority")

        if data["action"] not in ALLOWED_ACTIONS:
            raise ValueError("Invalid action")

        if not isinstance(data["is_important"], bool):
            raise ValueError("is_important must be a boolean")

        if not isinstance(data["summary"], str):
            raise ValueError("summary must be a string")

        if not data["summary"].strip():
            raise ValueError("summary cannot be empty")

        action = data["action"]
        priority = data["priority"]
        is_important = data["is_important"]

        if action == "ignore":
            if priority != "low":
                raise ValueError("ignore must have priority 'low'")
            if is_important is not False:
                raise ValueError("ignore must have is_important = false")

        elif action == "reply":
            if priority not in {"low", "medium"}:
                raise ValueError("reply must have priority 'low' or 'medium'")
            if is_important is not True:
                raise ValueError("reply must have is_important = true")

        elif action == "escalate":
            if priority != "high":
                raise ValueError("escalate must have priority 'high'")
            if is_important is not True:
                raise ValueError("escalate must have is_important = true")

        return data

    except Exception as e:
        print(f"Parsing error: {e}")
        return None