"""Assemble every app's state for a universe from its hand-written sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reference_environment.universes.apps import KartBazaarApp, StyleGaliApp
from reference_environment.universes.apps.common import parse_datetime

from .commerce import build_commerce
from .contacts import build_contacts_state, load_json
from .content import LIST_KEYS, load_content
from .dawaghar import build_dawaghar
from .everyday import build_calendar, build_chats, build_emails, build_sms
from .files import build_files
from .paysetu import build_paysetu
from .railmitra import build_railmitra
from .safarhub import build_safarhub
from .sehatcare import build_sehatcare
from .thalidash import build_thalidash


def people_index(cast: dict[str, Any], household: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Everyone with a person_id: the cast plus household members without a phone (Anaya)."""
    people = {p["person_id"]: p for p in cast["people"]}
    for member in household["members"] + household["relatives_for_bookings"]:
        people.setdefault(
            member["person_id"],
            {"full_name": member["full_name"], "age": member["age_on_today"], "gender": member["gender"]},
        )
    return people


def _with_defaults(
    content: dict[str, dict[str, Any]], cast: dict[str, Any], household: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Every app's content, empty where no storyline has written it yet, so a partly written universe builds."""
    today = household["today"]
    owner = next(p for p in cast["people"] if p["relationship"] == "self")
    store_defaults = {"delivery_days": 3, "cod_available": True, "return_policy": "refund", "return_window_days": 7}
    defaults: dict[str, dict[str, Any]] = {
        "emails": {"user_email": owner["email"]},
        "kartbazaar": {"defaults": {"seller": "KartBazaar Retail", **store_defaults}},
        "stylegali": {"defaults": {"seller": "StyleGali Marketplace", **store_defaults}},
        "railmitra": {"availability_window": {"start": today, "end": today}, "quota_share": {"GN": 1.0}},
        "sehatcare": {"slot_window": {"start": today, "end": today}},
    }
    apps = ("chats", "sms", "emails", "calendar", "paysetu", "thalidash", "sehatcare", "dawaghar")
    apps += ("kartbazaar", "stylegali", "safarhub", "railmitra")
    result = dict(content)
    for app in apps:
        empty: dict[str, Any] = {key: [] for key in LIST_KEYS}
        result[app] = {**empty, "conversations": {}, **defaults.get(app, {}), **content.get(app, {})}
    return result


def build_states(universe_dir: Path) -> dict[str, dict[str, Any]]:
    """Return {app_name: state} for every app. Apps no storyline has written yet start empty."""
    cast = load_json(universe_dir / "cast.json")
    household = load_json(universe_dir / "household.json")
    content = _with_defaults(load_content(universe_dir), cast, household)
    now = parse_datetime(household["now"]).timestamp()
    addresses = {address["address_key"]: address for address in household["addresses"]}
    user_phone = next(p["whatsapp_number"] for p in cast["people"] if p["relationship"] == "self")
    people = people_index(cast, household)

    thalidash, food_payments = build_thalidash(content["thalidash"], addresses, user_phone)
    sehatcare, health_payments = build_sehatcare(content["sehatcare"], people, addresses, user_phone)
    dawaghar, medicine_payments = build_dawaghar(content["dawaghar"], addresses, user_phone)
    phones = {p["person_id"]: p["whatsapp_number"] for p in cast["people"]}
    kartbazaar, kart_payments = build_commerce(content["kartbazaar"], KartBazaarApp, addresses, phones)
    stylegali, style_payments = build_commerce(content["stylegali"], StyleGaliApp, addresses, phones)
    household_people = {m["person_id"]: m for m in household["members"] + household["relatives_for_bookings"]}
    safarhub, travel_payments = build_safarhub(content["safarhub"], household_people)
    generated = food_payments + health_payments + medicine_payments + kart_payments + style_payments + travel_payments
    paysetu, txn_ids = build_paysetu(content["paysetu"], generated)
    linked = (
        thalidash["orders"],
        sehatcare["appointments"],
        dawaghar["orders"],
        kartbazaar["orders"],
        stylegali["orders"],
        safarhub["bookings"],
    )
    for records in linked:
        for record in records.values():
            if record["txn_id"]:
                record["txn_id"] = txn_ids[record["txn_id"]]

    return {
        "Contacts": build_contacts_state(universe_dir),
        "Chats": build_chats(content.get("chats", {}), cast, now),
        "Messages": build_sms(content.get("sms", {}), cast, now),
        "Emails": build_emails(content["emails"], now),
        "Calendar": build_calendar(content.get("calendar", {})),
        "Files": build_files(universe_dir),
        "PaySetu": paysetu,
        "ThaliDash": thalidash,
        "SehatCare": sehatcare,
        "DawaGhar": dawaghar,
        "KartBazaar": kartbazaar,
        "StyleGali": stylegali,
        "SafarHub": safarhub,
        "RailMitra": build_railmitra(content["railmitra"], household_people),
    }
