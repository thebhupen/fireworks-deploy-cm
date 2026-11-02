"""Build ARE Contacts app state from a universe's hand-written cast.json and household.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _address_text(address: dict[str, Any]) -> str:
    return f"{address['line1']}, {address['area']}, {address['city']} {address['pincode']}"


def _description(person: dict[str, Any], styles: dict[str, str], entry_index: int) -> str:
    parts = [
        f"relationship: {person['relationship']}",
        f"full name: {person['full_name']}",
        f"style: {styles[person['writing_style']]}",
    ]
    if entry_index > 0:
        parts.append(f"notes: second number ({person['entries'][entry_index]['operator']})")
    else:
        parts.append(f"notes: {person['notes']}")
    return "; ".join(parts)


def build_contacts_state(universe_dir: Path, view_limit: int = 10) -> dict[str, Any]:
    """Return {"contacts": {...}, "view_limit": n} in the shape ARE's ContactsApp.load_state expects."""
    cast = load_json(universe_dir / "cast.json")
    household = load_json(universe_dir / "household.json")
    addresses = {address["address_key"]: address for address in household["addresses"]}
    contacts: dict[str, dict[str, Any]] = {}
    for person in cast["people"]:
        address = _address_text(addresses[person["address_key"]]) if person["address_key"] else person["lives_in"]
        for index, entry in enumerate(person["entries"]):
            primary = index == 0
            contacts[entry["contact_id"]] = {
                "contact_id": entry["contact_id"],
                "first_name": entry["first_name"],
                "last_name": entry["last_name"],
                "is_user": bool(entry.get("is_user", False)),
                "gender": person["gender"] if primary else "Unknown",
                "age": person["age"] if primary else None,
                "nationality": "Indian" if primary and person["person_id"].startswith("PRS-") else None,
                "city_living": person["city"] if primary else None,
                "country": "India" if primary else None,
                "status": person["status"] if primary else "Unknown",
                "job": person["job"] if primary else None,
                "description": _description(person, cast["styles"], index),
                "phone": entry["phone"],
                "email": person["email"] if primary else None,
                "address": address if primary else None,
            }
    return {"contacts": contacts, "view_limit": view_limit}
