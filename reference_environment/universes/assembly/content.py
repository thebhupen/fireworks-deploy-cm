"""Load a universe's hand-written content, one folder per storyline, merged per app file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contacts import load_json

LIST_KEYS = (
    "restaurants",
    "coupons",
    "orders",
    "reservations",
    "walk_in_meals",
    "addresses",
    "sources",
    "payees",
    "transactions",
    "requests",
    "external_members",
    "senders",
    "emails",
    "events",
    "providers",
    "doctors",
    "lab_tests",
    "slot_templates",
    "taken_slots",
    "past_slots",
    "patients",
    "appointments",
    "medical_records",
    "medicines",
    "prescriptions",
    "refill_reminders",
    "products",
    "discount_codes",
    "wishlist",
    "saved_travellers",
    "hotels",
    "room_sales",
    "packages",
    "airports",
    "flights",
    "fare_pricing",
    "flight_sales",
    "bookings",
    "stations",
    "trains",
    "availability_templates",
    "availability_overrides",
    "saved_passengers",
)


def storyline_dirs(universe_dir: Path) -> list[Path]:
    return sorted(path for path in (universe_dir / "content").iterdir() if path.is_dir())


def load_content(universe_dir: Path) -> dict[str, dict[str, Any]]:
    """Return {"thalidash": {...}, "chats": {...}, ...} with lists concatenated across storylines.

    Conversations with the same id are merged message by message, so a chat can grow across storylines.
    """
    merged: dict[str, dict[str, Any]] = {}
    for folder in storyline_dirs(universe_dir):
        for path in sorted(folder.glob("*.json")):
            data = load_json(path)
            target = merged.setdefault(path.stem, {"conversations": {}})
            for key in LIST_KEYS:
                if key in data:
                    target.setdefault(key, []).extend(data[key])
            for key in ("user_email", "subscription", "slot_window", "defaults", "availability_window", "quota_share"):
                if key in data:
                    if target.get(key, data[key]) != data[key]:
                        raise ValueError(f"{path}: {key} differs from an earlier storyline")
                    target[key] = data[key]
            for conversation in data.get("conversations", []):
                existing = target["conversations"].get(conversation["conversation_id"])
                if existing is None:
                    target["conversations"][conversation["conversation_id"]] = {
                        **conversation,
                        "messages": list(conversation["messages"]),
                    }
                    continue
                if set(existing["participants"]) != set(conversation["participants"]):
                    raise ValueError(f"{path}: participants of {conversation['conversation_id']} differ")
                existing["messages"].extend(conversation["messages"])
    return merged


def unique(records: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if record[key] in result:
            raise ValueError(f"Duplicate {label} {record[key]}")
        result[record[key]] = record
    return result
