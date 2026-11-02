"""RailMitra state: stations, trains, generated seat availability per run, and saved passengers."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from reference_environment.universes.apps.common import parse_date

from .content import unique

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _key(train_number: str, start: str, travel_class: str, quota: str) -> str:
    return f"{train_number}|{start}|{travel_class}|{quota}"


def build_railmitra(content: dict[str, Any], household_people: dict[str, dict[str, Any]]) -> dict[str, Any]:
    stations = unique(content.get("stations", []), "code", "station")
    trains = unique(content.get("trains", []), "train_number", "train")
    for train in trains.values():
        for stop in train["stops"]:
            if stop["station_code"] not in stations:
                raise ValueError(f"Train {train['train_number']} stops at unknown station {stop['station_code']}")
    window = content["availability_window"]
    first, last = parse_date(window["start"]), parse_date(window["end"])
    share = content["quota_share"]
    availability: dict[str, dict[str, Any]] = {}
    for template in content.get("availability_templates", []):
        for train_number in template["train_numbers"]:
            train = trains[train_number]
            day = first
            while day <= last:
                if WEEKDAYS[day.weekday()] in train["runs_on"]:
                    for travel_class, (seats, rac, waitlist) in template["seats"].items():
                        for quota in template["quotas"]:
                            ratio = share[quota]
                            key = _key(train_number, day.isoformat(), travel_class, quota)
                            availability[key] = {
                                "train_number": train_number,
                                "start_date": day.isoformat(),
                                "travel_class": travel_class,
                                "quota": quota,
                                "seats_available": round(seats * ratio),
                                "rac_available": rac if quota == "GN" else 0,
                                "waitlist_count": 0,
                                "waitlist_limit": max(round(waitlist * ratio), 10),
                                "seats_allotted": 0,
                                "rac_allotted": 0,
                            }
                day += timedelta(days=1)
    for override in content.get("availability_overrides", []):
        key = _key(override["train_number"], override["start_date"], override["travel_class"], override["quota"])
        if key not in availability:
            raise ValueError(f"Availability override for a run that does not exist: {key}")
        availability[key].update({k: v for k, v in override.items() if k not in ("train_number", "start_date")})
    passengers = {}
    for passenger in content.get("saved_passengers", []):
        person = household_people[passenger["person_id"]]
        passengers[passenger["passenger_id"]] = {
            "passenger_id": passenger["passenger_id"],
            "name": person["full_name"],
            "age": person["age_on_today"],
            "gender": person["gender"],
            "berth_preference": passenger["berth_preference"],
        }
    return {
        "id_counters": {"RM-PAX": len(passengers), "PNR": 0},
        "stations": stations,
        "trains": trains,
        "availability": availability,
        "saved_passengers": passengers,
        "bookings": {},
        "run_changes": {},
    }
