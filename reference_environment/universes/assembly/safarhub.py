"""SafarHub state: travellers from the household record, stays, packages, flights and past bookings."""

from __future__ import annotations

from typing import Any

from .content import unique


def build_safarhub(
    content: dict[str, Any], household_people: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (SafarHub state, PaySetu payments with local keys)."""
    travellers = {}
    for traveller in content.get("saved_travellers", []):
        person = household_people[traveller["person_id"]]
        travellers[traveller["traveller_id"]] = {
            "traveller_id": traveller["traveller_id"],
            "name": person["full_name"],
            "date_of_birth": person["date_of_birth"],
            "gender": person["gender"],
            "type": traveller["type"],
        }
    hotels = {
        h["hotel_id"]: {"tags": [], "check_in_time": "14:00", "check_out_time": "11:00", **h}
        for h in unique(content.get("hotels", []), "hotel_id", "hotel").values()
    }
    room_sales: dict[str, int] = {}
    for sale in content.get("room_sales", []):
        hotel = hotels[sale["hotel_id"]]
        room = next(r for r in hotel["room_types"] if r["room_type"] == sale["room_type"])
        key = f"{sale['hotel_id']}|{sale['room_type']}|{sale['date']}"
        room_sales[key] = room_sales.get(key, 0) + sale["rooms"]
        if room_sales[key] > room["rooms_total"]:
            raise ValueError(f"More {sale['room_type']} rooms sold than exist at {hotel['name']} on {sale['date']}")
    packages = {
        p["package_id"]: {"description": "", **p}
        for p in unique(content.get("packages", []), "package_id", "package").values()
    }
    for package in packages.values():
        if set(package["slots_left"]) != set(package["available_start_dates"]):
            raise ValueError(f"{package['package_id']}: slots_left must cover exactly the start dates")
    airports = unique(content.get("airports", []), "code", "airport")
    flights = {
        f["flight_id"]: {"arrival_day_offset": 0, "stops": [], **f}
        for f in unique(content.get("flights", []), "flight_id", "flight").values()
    }
    fare_pricing = {
        r["rule_id"]: {"label": "", "festival": False, **r}
        for r in unique(content.get("fare_pricing", []), "rule_id", "fare rule").values()
    }
    flight_sales = {f"{s['flight_id']}|{s['date']}": s["seats"] for s in content.get("flight_sales", [])}
    bookings, payments = {}, []
    for booking in unique(content.get("bookings", []), "booking_id", "booking").values():
        key = f"travel:{booking['booking_id']}"
        payments.append(
            {
                "key": key,
                "timestamp": booking["booked_at"],
                "direction": "debit",
                "amount": booking["amount"],
                "counterparty_name": "SafarHub",
                "source_id": booking["payment"],
                "category": "travel",
                "reference_app": "SafarHub",
                "reference_id": booking["booking_id"],
            }
        )
        bookings[booking["booking_id"]] = {
            "booking_id": booking["booking_id"],
            "type": booking["type"],
            "item_id": booking["item_id"],
            "details": booking["details"],
            "traveller_ids": list(booking.get("traveller_ids", [])),
            "amount": booking["amount"],
            "txn_id": key,
            "booked_at": booking["booked_at"],
            "status": booking.get("status", "completed"),
            "refunded_amount": 0,
        }
    state = {
        "id_counters": {"SH-BK": len(bookings), "SH-TRV": len(travellers)},
        "airports": airports,
        "flights": flights,
        "fare_pricing": fare_pricing,
        "flight_sales": flight_sales,
        "flight_changes": {},
        "hotels": hotels,
        "room_sales": room_sales,
        "packages": packages,
        "saved_travellers": travellers,
        "bookings": bookings,
    }
    return state, payments
