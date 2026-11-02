"""Cross-app consistency checks (universe_spec.md section 7). Returns a list of problems; empty means valid."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from reference_environment.universes.apps.common import parse_datetime

from .contacts import load_json
from .files import file_paths

ASSAMESE_SCRIPT = re.compile(r"[ঀ-৿]")
BOTH_SCRIPTS = "assamese_both_scripts"
SCRIPT_WITH_PARENTS = "mixed_home_script"


def validate(universe_dir: Path, states: dict[str, dict[str, Any]]) -> list[str]:
    cast = load_json(universe_dir / "cast.json")
    household = load_json(universe_dir / "household.json")
    now = parse_datetime(household["now"])
    problems: list[str] = []

    def past(label: str, moment: str) -> None:
        if parse_datetime(moment) > now:
            problems.append(f"{label} is dated {moment}, after now ({household['now']})")

    descriptions = " ".join(event["description"] for event in states["Calendar"]["events"].values())
    pay = states["PaySetu"]
    food = states["ThaliDash"]
    txns = pay["transactions"]

    # Rule 2: every paid order has exactly one matching charge.
    for order in food["orders"].values():
        past(f"ThaliDash {order['order_id']}", order["placed_at"])
        if order["payment"] == "cod":
            continue
        txn = txns.get(order["txn_id"])
        if txn is None:
            problems.append(f"{order['order_id']} has no PaySetu transaction")
            continue
        expected = (order["total"], "ThaliDash", order["order_id"], order["payment"])
        actual = (txn["amount"], txn["reference_app"], txn["reference_id"], txn["source_id"])
        if expected != actual:
            problems.append(f"{order['order_id']} charge mismatch: {expected} vs {actual}")
    charged = [
        t["reference_id"] for t in txns.values() if t["reference_app"] == "ThaliDash" and t["direction"] == "debit"
    ]
    if len(charged) != len(set(charged)):
        problems.append("A ThaliDash order is charged more than once")

    # Rule 2 for health: appointments and medicine orders are charged exactly what they cost.
    charged_records = [
        ("SehatCare", states["SehatCare"]["appointments"], "amount", "booked_at"),
        ("DawaGhar", states["DawaGhar"]["orders"], "total", "placed_at"),
        ("KartBazaar", states["KartBazaar"]["orders"], "total", "placed_at"),
        ("StyleGali", states["StyleGali"]["orders"], "total", "placed_at"),
        ("SafarHub", states["SafarHub"]["bookings"], "amount", "booked_at"),
    ]
    for app, records, amount_key, time_key in charged_records:
        for record_id, record in records.items():
            past(f"{app} {record_id}", record[time_key])
            if not record["txn_id"]:
                if record.get("payment") != "cod" and record.get("status") != "on_hold_prescription":
                    problems.append(f"{app} {record_id} has no PaySetu transaction")
                continue
            txn = txns[record["txn_id"]]
            if (txn["amount"], txn["reference_app"], txn["reference_id"]) != (record[amount_key], app, record_id):
                problems.append(f"{app} {record_id} charge mismatch")

    # Rule 4 for health: every appointment is on the calendar.
    for appointment_id in states["SehatCare"]["appointments"]:
        if appointment_id not in descriptions:
            problems.append(f"Appointment {appointment_id} has no calendar event")

    # Rule 4 for travel: every SafarHub booking is on the calendar.
    for booking_id in states["SafarHub"]["bookings"]:
        if booking_id not in descriptions:
            problems.append(f"Booking {booking_id} has no calendar event")

    # Documents referred to by records and prescriptions exist in Files.
    documents = file_paths(universe_dir)
    referring = list(states["SehatCare"]["medical_records"].values()) + list(
        states["DawaGhar"]["prescriptions"].values()
    )
    for record in referring:
        if record.get("file_path") and record["file_path"] not in documents:
            problems.append(
                f"{record.get('record_id') or record['prescription_id']} points to missing {record['file_path']}"
            )

    # A lab package bundles tests the same lab sells on its own, by test_id: booking one books each of them.
    lab_tests = states["SehatCare"]["lab_tests"]
    for test in lab_tests.values():
        for included in test["includes"]:
            inner = lab_tests.get(included)
            if inner is None or inner["provider_id"] != test["provider_id"] or included == test["test_id"]:
                problems.append(
                    f"Lab test {test['test_id']} includes {included!r}, which is not the test_id of another test "
                    f"of {test['provider_id']}. List test_ids only; put what a test measures in its description"
                )

    # Rule 9 for patients: name, age and gender match the household or cast.
    people = {p["full_name"]: (p["age"], p["gender"]) for p in cast["people"]}
    people.update({m["full_name"]: (m["age_on_today"], m["gender"]) for m in household["members"]})
    for patient in states["SehatCare"]["patients"].values():
        if people.get(patient["name"]) != (patient["age"], patient["gender"]):
            problems.append(f"Patient {patient['patient_id']} does not match the household record")
    born = {
        m["full_name"]: (m["date_of_birth"], m["gender"])
        for m in household["members"] + household["relatives_for_bookings"]
    }
    for traveller in states["SafarHub"]["saved_travellers"].values():
        if born.get(traveller["name"]) != (traveller["date_of_birth"], traveller["gender"]):
            problems.append(f"Traveller {traveller['traveller_id']} does not match the household record")
    ages = {
        m["full_name"]: (m["age_on_today"], m["gender"])
        for m in household["members"] + household["relatives_for_bookings"]
    }
    for passenger in states["RailMitra"]["saved_passengers"].values():
        if ages.get(passenger["name"]) != (passenger["age"], passenger["gender"]):
            problems.append(f"Passenger {passenger['passenger_id']} does not match the household record")
    for prescription in states["DawaGhar"]["prescriptions"].values():
        if prescription["patient_name"] not in people:
            problems.append(f"{prescription['prescription_id']} is for unknown patient {prescription['patient_name']}")

    # A paid money request has exactly one payment that references it.
    for request in pay["requests"].values():
        payments = [
            t for t in txns.values() if t["reference_id"] == request["request_id"] and t["direction"] == "debit"
        ]
        if request["status"] == "paid" and request["direction"] == "incoming":
            if [t["amount"] for t in payments] != [request["amount"]]:
                problems.append(f"{request['request_id']} is paid but has no single matching payment")
        elif payments:
            problems.append(f"{request['request_id']} is {request['status']} but has a payment")

    # Rule 3: history is not in the future.
    for txn in txns.values():
        past(f"PaySetu {txn['txn_id']}", txn["timestamp"])
    for request in pay["requests"].values():
        past(f"PaySetu {request['request_id']}", request["created_at"])

    # Rule 4: every dated booking has a calendar event that names it.

    for reservation_id in food["reservations"]:
        if reservation_id not in descriptions:
            problems.append(f"Reservation {reservation_id} has no calendar event")

    # Payees: a transfer to a saved UPI ID uses the payee's saved name.
    payees = {p["upi_id"]: p["name"] for p in pay["payees"].values()}
    for txn in txns.values():
        upi = txn.get("counterparty_upi_id")
        if upi in payees and txn["counterparty_name"] != payees[upi]:
            problems.append(f"{txn['txn_id']} names {txn['counterparty_name']} but {upi} is saved as {payees[upi]}")

    # Rule 6 (script part): Assamese script only from people who write in both scripts.
    both = {p["whatsapp_number"] for p in cast["people"] if p["writing_style"] == BOTH_SCRIPTS}
    with_parents = {p["whatsapp_number"] for p in cast["people"] if p["writing_style"] == SCRIPT_WITH_PARENTS}
    for app in ("Chats", "Messages"):
        for conversation in states[app]["conversations"].values():
            parents_present = bool(both & set(conversation["participant_ids"]))
            for message in conversation["messages"]:
                sender = message["sender_id"]
                allowed = sender in both or (sender in with_parents and parents_present)
                if ASSAMESE_SCRIPT.search(message["content"]) and not allowed:
                    problems.append(f"{app} {message['message_id']} uses Assamese script from {sender}")

    # Calendar attendees are known people.
    known = {p["full_name"] for p in cast["people"]} | {m["full_name"] for m in household["members"]}
    for event in states["Calendar"]["events"].values():
        for attendee in event["attendees"]:
            if attendee not in known:
                problems.append(f"Calendar {event['event_id']} lists unknown attendee {attendee}")

    # Rule 9: saved addresses match the household record.
    canonical = {(a["line1"], a["pincode"]) for a in household["addresses"]}
    saved_addresses = [
        *food["addresses"].values(),
        *states["SehatCare"]["addresses"].values(),
        *states["DawaGhar"]["addresses"].values(),
        *states["KartBazaar"]["addresses"].values(),
        *states["StyleGali"]["addresses"].values(),
    ]
    for address in saved_addresses:
        if (address["line1"], address["pincode"]) not in canonical:
            problems.append(f"Saved address {address['address_id']} differs from household.json")

    # Rule 8: fictional identifiers only.
    for email in (e for folder in states["Emails"]["folders"].values() for e in folder["emails"]):
        for address in [email["sender"], *email["recipients"], *email["cc"]]:
            if not address.endswith("example.test"):
                problems.append(f"Email {email['email_id']} uses a non-fictional address {address}")
    return problems
