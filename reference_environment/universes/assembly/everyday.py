"""State for ARE's reused apps: Chats and Messages (MessagingAppV2), Emails (EmailClientV2), Calendar."""

from __future__ import annotations

from typing import Any

from reference_environment.universes.apps.common import parse_datetime

from .content import unique

STRFTIME = "%A, %Y-%m-%d %H:%M:%S"
EMAIL_FOLDERS = ("INBOX", "SENT", "DRAFT", "TRASH")


def epoch(moment: str) -> float:
    return parse_datetime(moment).timestamp()


def saved_name(person: dict[str, Any], phone: str) -> str:
    for entry in person["entries"]:
        if entry["phone"] == phone:
            return f"{entry['first_name']} {entry['last_name']}".strip()
    raise ValueError(f"{person['person_id']} has no entry for {phone}")


def _conversations(
    raw: dict[str, dict[str, Any]], resolve: dict[str, str], names: dict[str, str], today: float
) -> dict[str, dict[str, Any]]:
    conversations = {}
    for conversation_id, conversation in raw.items():
        participants = [resolve[member] for member in conversation["participants"]]
        messages = []
        for index, (moment, sender, text) in enumerate(sorted(conversation["messages"], key=lambda m: m[0]), 1):
            if sender not in conversation["participants"]:
                raise ValueError(f"{conversation_id}: {sender} is not a participant")
            stamp = epoch(moment)
            if stamp > today:
                raise ValueError(f"{conversation_id}: message at {moment} is after today")
            messages.append(
                {
                    "sender_id": resolve[sender],
                    "message_id": f"{conversation_id}-{index:03d}",
                    "timestamp": stamp,
                    "content": text,
                }
            )
        others = [names[p] for p in participants if p != participants[0]]
        conversations[conversation_id] = {
            "participant_ids": participants,
            "messages": messages,
            "title": conversation.get("title") or ", ".join(others),
            "conversation_id": conversation_id,
            "last_updated": messages[-1]["timestamp"] if messages else today,
        }
    return conversations


def _messaging_state(mode: str, user_id: str, names: dict[str, str], conversations: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversations": conversations,
        "messages_view_limit": 10,
        "conversation_view_limit": 5,
        "mode": mode,
        "name_to_id": {name: member_id for member_id, name in names.items()},
        "id_to_name": dict(names),
        "current_user_id": user_id,
        "current_user_name": names[user_id],
    }


def build_chats(content: dict[str, Any], cast: dict[str, Any], today: float) -> dict[str, Any]:
    """WhatsApp: one id per person (their WhatsApp number), shown under the name it is saved as."""
    resolve, names = {}, {}
    for person in cast["people"]:
        number = person["whatsapp_number"]
        resolve[person["person_id"]] = number
        names[number] = person["full_name"] if person["relationship"] == "self" else saved_name(person, number)
    for member in content.get("external_members", []):
        resolve[member["member_id"]] = member["number"]
        names[member["number"]] = member["name"]
    user = resolve[next(p["person_id"] for p in cast["people"] if p["relationship"] == "self")]
    conversations = _conversations(content.get("conversations", {}), resolve, names, today)
    for conversation in conversations.values():
        conversation["participant_ids"].sort(key=lambda member: member != user)
    return _messaging_state("NAME", user, names, conversations)


def build_sms(content: dict[str, Any], cast: dict[str, Any], today: float) -> dict[str, Any]:
    """SMS: every phonebook entry is its own number; businesses use sender codes."""
    resolve, names = {}, {}
    for person in cast["people"]:
        for entry in person["entries"]:
            resolve[entry["contact_id"]] = entry["phone"]
            names[entry["phone"]] = f"{entry['first_name']} {entry['last_name']}".strip()
            if entry.get("is_user"):
                resolve["USER"] = entry["phone"]
                names[entry["phone"]] = person["full_name"]
    for sender in content.get("senders", []):
        resolve[sender["sender_id"]] = sender["sender_id"]
        names[sender["sender_id"]] = sender["name"]
    conversations = _conversations(content.get("conversations", {}), resolve, names, today)
    return _messaging_state("PHONE_NUMBER", resolve["USER"], names, conversations)


def build_emails(content: dict[str, Any], today: float) -> dict[str, Any]:
    folders = {name: {"folder_name": name, "emails": []} for name in EMAIL_FOLDERS}
    emails = unique(content.get("emails", []), "email_id", "email")
    for email in sorted(emails.values(), key=lambda e: e["timestamp"], reverse=True):
        stamp = epoch(email["timestamp"])
        if stamp > today:
            raise ValueError(f"{email['email_id']} is after today")
        if email.get("parent_id") and email["parent_id"] not in emails:
            raise ValueError(f"{email['email_id']} replies to unknown {email['parent_id']}")
        folders[email["folder"]]["emails"].append(
            {
                "sender": email["sender"],
                "recipients": list(email["recipients"]),
                "subject": email["subject"],
                "content": email["content"],
                "email_id": email["email_id"],
                "parent_id": email.get("parent_id"),
                "cc": list(email.get("cc", [])),
                "attachments": {},
                "timestamp": stamp,
                "is_read": email.get("is_read", True),
            }
        )
    return {"user_email": content["user_email"], "view_limit": 5, "folders": folders}


def build_calendar(content: dict[str, Any]) -> dict[str, Any]:
    events = {}
    for event in unique(content.get("events", []), "event_id", "calendar event").values():
        start, end = parse_datetime(event["start"]), parse_datetime(event["end"])
        if end <= start:
            raise ValueError(f"{event['event_id']} ends before it starts")
        events[event["event_id"]] = {
            "event_id": event["event_id"],
            "title": event["title"],
            "start_datetime": start.timestamp(),
            "end_datetime": end.timestamp(),
            "tag": event.get("tag"),
            "description": event.get("description", ""),
            "location": event.get("location", ""),
            "attendees": list(event.get("attendees", [])),
            "start_strftime": start.strftime(STRFTIME),
            "end_strftime": end.strftime(STRFTIME),
        }
    return {"events": events}
