"""RailMitra: train booking modelled on IRCTC, with simplified rules.

Schema: app_schemas.md section 2.

Simplifications, all deterministic:
- Availability is per train run, class and quota; it does not vary by segment.
- A cancelled seat is not handed back to the pool. Waitlist movement is driven
  only by environment events, so scenarios control it exactly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from are.simulation.tool_utils import OperationType, app_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import type_check

from .common import (
    BharatApp,
    dump_records,
    load_records,
    matches,
    parse_date,
    percent_of,
    round_to_nearest,
    to_dict,
)

ADVANCE_BOOKING_DAYS = 60
MAX_PASSENGERS = {"GN": 6, "TQ": 4, "SS": 2, "LD": 6}
QUOTAS = tuple(MAX_PASSENGERS)
CLASSES = ("1A", "2A", "3A", "SL", "CC", "2S")
AC_CLASSES = ("1A", "2A", "3A", "CC")
TATKAL_OPENS = {True: time(10, 0), False: time(11, 0)}
FLAT_CANCELLATION = {"1A": 240, "2A": 200, "3A": 180, "SL": 120, "CC": 180, "2S": 60}
WAITLIST_CLERKAGE = 60
COACH_PREFIX = {"1A": "H", "2A": "A", "3A": "B", "SL": "S", "CC": "C", "2S": "D"}
BERTH_PATTERN = {
    "1A": ["LB", "UB"],
    "2A": ["LB", "UB", "LB", "UB", "SL", "SU"],
    "3A": ["LB", "MB", "UB", "LB", "MB", "UB", "SL", "SU"],
    "SL": ["LB", "MB", "UB", "LB", "MB", "UB", "SL", "SU"],
    "CC": ["WS", "MS", "AS"],
    "2S": ["WS", "MS", "AS"],
}
BERTHS_PER_COACH = {"1A": 24, "2A": 48, "3A": 64, "SL": 72, "CC": 78, "2S": 108}
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass
class Station:
    code: str
    name: str
    city: str
    state: str


@dataclass
class Train:
    train_number: str
    name: str
    runs_on: list[str]
    stops: list[dict[str, Any]]
    classes: list[str]
    fare_rules: dict[str, dict[str, Any]]


@dataclass
class Availability:
    train_number: str
    start_date: str
    travel_class: str
    quota: str
    seats_available: int
    rac_available: int
    waitlist_count: int = 0
    waitlist_limit: int = 200
    seats_allotted: int = 0
    rac_allotted: int = 0


@dataclass
class SavedPassenger:
    passenger_id: str
    name: str
    age: int
    gender: str
    berth_preference: str = "none"


@dataclass
class Booking:
    pnr: str
    train_number: str
    journey_date: str
    from_station: str
    to_station: str
    travel_class: str
    quota: str
    passengers: list[dict[str, Any]]
    total_fare: int
    txn_id: str
    booked_at: str
    status: str = "booked"
    chart_prepared: bool = False
    refunded_amount: int = 0


@dataclass
class TrainRunChange:
    delay_minutes: int = 0
    cancelled: bool = False


def _availability_key(train_number: str, start_date: str, travel_class: str, quota: str) -> str:
    return f"{train_number}|{start_date}|{travel_class}|{quota}"


def _run_key(train_number: str, start_date: str) -> str:
    return f"{train_number}|{start_date}"


class RailMitraApp(BharatApp):
    """
    RailMitra books Indian Railways train tickets.

    Notes:
        - Stations are named by their station code, e.g. "SBC" (KSR Bengaluru), "DBRG" (Dibrugarh).
          Use search_stations to find codes.
        - journey_date is the date the passenger boards at from_station, format YYYY-MM-DD.
        - Classes: 1A, 2A, 3A, SL, CC, 2S. Quotas: GN (general), TQ (Tatkal), SS (senior citizen), LD (ladies).
        - Booking opens 60 days before the journey date (the journey date itself is not counted).
        - Tatkal (TQ) opens the day before the journey at 10:00 for AC classes and 11:00 for SL and 2S;
          at most 4 passengers, and confirmed Tatkal tickets get no refund on cancellation.
        - At most 6 passengers per general booking. Children under 5 travel free without a berth
          and are not booked as passengers.
        - Availability is shown as AVAILABLE-n, RAC-n, WL-n or REGRET. A booking with REGRET fails;
          RAC and WL bookings succeed and carry that status.
        - Cancellation charge per passenger for confirmed or RAC tickets: more than 48 h before departure,
          a flat fee by class (1A 240, 2A 200, 3A 180, SL 120, CC 180, 2S 60 rupees); 48 h to 12 h, 25% of fare;
          12 h to 4 h, 50% of fare (never below the flat fee); under 4 h or after the chart is prepared, no refund.
          Fully waitlisted passengers are refunded the fare minus 60 rupees.
        - Times are local (IST). Amounts are whole rupees.
    """

    def __init__(self, name: str | None = "RailMitra") -> None:
        super().__init__(name)
        self.stations: dict[str, Station] = {}
        self.trains: dict[str, Train] = {}
        self.availability: dict[str, Availability] = {}
        self.saved_passengers: dict[str, SavedPassenger] = {}
        self.bookings: dict[str, Booking] = {}
        self.run_changes: dict[str, TrainRunChange] = {}

    # State -----------------------------------------------------------------
    def get_state(self) -> dict[str, Any]:
        return {
            **self.base_state(),
            "stations": dump_records(self.stations),
            "trains": dump_records(self.trains),
            "availability": dump_records(self.availability),
            "saved_passengers": dump_records(self.saved_passengers),
            "bookings": dump_records(self.bookings),
            "run_changes": dump_records(self.run_changes),
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self.load_base_state(state_dict)
        self.stations = load_records(Station, state_dict.get("stations", {}))
        self.trains = load_records(Train, state_dict.get("trains", {}))
        self.availability = load_records(Availability, state_dict.get("availability", {}))
        self.saved_passengers = load_records(SavedPassenger, state_dict.get("saved_passengers", {}))
        self.bookings = load_records(Booking, state_dict.get("bookings", {}))
        self.run_changes = load_records(TrainRunChange, state_dict.get("run_changes", {}))

    # Internal helpers --------------------------------------------------------
    def _train(self, train_number: str) -> Train:
        if train_number not in self.trains:
            raise ValueError(f"Train {train_number} does not exist")
        return self.trains[train_number]

    @staticmethod
    def _stop(train: Train, station_code: str) -> dict[str, Any]:
        for stop in train.stops:
            if stop["station_code"] == station_code:
                return stop
        raise ValueError(f"Train {train.train_number} does not stop at {station_code}")

    def _segment(self, train: Train, from_station: str, to_station: str) -> tuple[dict, dict]:
        board, alight = self._stop(train, from_station), self._stop(train, to_station)
        if train.stops.index(board) >= train.stops.index(alight):
            raise ValueError(f"Train {train.train_number} does not run from {from_station} to {to_station}")
        return board, alight

    def _start_date(self, train: Train, board: dict[str, Any], journey_date: str) -> date:
        """Date the train leaves its origin, for a passenger boarding on journey_date."""
        start = parse_date(journey_date) - timedelta(days=board["day_offset"])
        if WEEKDAYS[start.weekday()] not in train.runs_on:
            raise ValueError(f"Train {train.train_number} does not leave {board['station_code']} on {journey_date}")
        return start

    def _change(self, train_number: str, start: date) -> TrainRunChange:
        return self.run_changes.get(_run_key(train_number, start.isoformat()), TrainRunChange())

    def _event_time(self, start: date, stop: dict[str, Any], kind: str, delay: int) -> datetime:
        clock = stop[kind] or stop["departure"] or stop["arrival"]
        hours, minutes = (int(part) for part in clock.split(":"))
        day = start + timedelta(days=stop["day_offset"])
        moment = datetime(day.year, day.month, day.day, hours, minutes, tzinfo=timezone.utc)
        return moment + timedelta(minutes=delay)

    def _fare(self, train: Train, board: dict, alight: dict, travel_class: str, quota: str) -> int:
        if travel_class not in train.classes:
            raise ValueError(f"Train {train.train_number} has no {travel_class} class")
        rules = train.fare_rules[travel_class]
        distance = alight["distance_km"] - board["distance_km"]
        fare = round_to_nearest(rules["rate_per_km"] * distance, 5) + rules["reservation_charge"]
        if quota == "TQ":
            fare += rules["tatkal_surcharge"]
        return fare

    def _slot(self, train_number: str, start: date, travel_class: str, quota: str) -> Availability:
        key = _availability_key(train_number, start.isoformat(), travel_class, quota)
        if key not in self.availability:
            raise ValueError(
                f"No {quota} quota in {travel_class} on train {train_number} leaving origin {start.isoformat()}"
            )
        return self.availability[key]

    @staticmethod
    def _status_text(slot: Availability) -> str:
        if slot.seats_available > 0:
            return f"AVAILABLE-{slot.seats_available}"
        if slot.rac_available > 0:
            return f"RAC-{slot.rac_allotted + 1}"
        if slot.waitlist_count < slot.waitlist_limit:
            return f"WL-{slot.waitlist_count + 1}"
        return "REGRET"

    def _booking(self, pnr: str) -> Booking:
        if pnr not in self.bookings:
            raise ValueError(f"PNR {pnr} does not exist")
        return self.bookings[pnr]

    def _departure_for(self, booking: Booking) -> datetime:
        train = self._train(booking.train_number)
        board = self._stop(train, booking.from_station)
        start = parse_date(booking.journey_date) - timedelta(days=board["day_offset"])
        return self._event_time(start, board, "departure", self._change(train.train_number, start).delay_minutes)

    def _allocate(self, slot: Availability, count: int) -> list[tuple[str, str, int | None, str]]:
        """Return (booking_status, coach, berth, berth_type) per passenger, in order."""
        if slot.seats_available + slot.rac_available + (slot.waitlist_limit - slot.waitlist_count) < count:
            raise ValueError("Not enough availability for all passengers (REGRET)")
        allocations = []
        for _ in range(count):
            if slot.seats_available > 0:
                slot.seats_available -= 1
                slot.seats_allotted += 1
                number = slot.seats_allotted
                per_coach = BERTHS_PER_COACH[slot.travel_class]
                coach = f"{COACH_PREFIX[slot.travel_class]}{(number - 1) // per_coach + 1}"
                berth = (number - 1) % per_coach + 1
                pattern = BERTH_PATTERN[slot.travel_class]
                allocations.append(("CNF", coach, berth, pattern[(berth - 1) % len(pattern)]))
            elif slot.rac_available > 0:
                slot.rac_available -= 1
                slot.rac_allotted += 1
                allocations.append((f"RAC-{slot.rac_allotted}", "", None, ""))
            else:
                slot.waitlist_count += 1
                allocations.append((f"WL-{slot.waitlist_count}", "", None, ""))
        return allocations

    def _cancellation_refund(self, booking: Booking, passenger: dict[str, Any], hours: float) -> int:
        fare = passenger["fare"]
        status = passenger["current_status"]
        if status.startswith("WL"):
            return max(fare - WAITLIST_CLERKAGE, 0)
        if booking.quota == "TQ":
            return 0
        if booking.chart_prepared or hours < 4:
            return 0
        flat = FLAT_CANCELLATION[booking.travel_class]
        if hours < 12:
            charge = max(percent_of(fare, 50), flat)
        elif hours < 48:
            charge = max(percent_of(fare, 25), flat)
        else:
            charge = flat
        return max(fare - charge, 0)

    def _refund_booking(self, booking: Booking, amount: int) -> None:
        if amount > 0:
            self.refund(booking.txn_id, amount)
            booking.refunded_amount += amount

    @staticmethod
    def _update_booking_status(booking: Booking) -> None:
        active = [p for p in booking.passengers if p["current_status"] != "CAN"]
        booking.status = (
            "cancelled"
            if not active
            else ("partially_cancelled" if len(active) < len(booking.passengers) else "booked")
        )

    # Read tools --------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_stations(self, query: str) -> list[dict[str, Any]]:
        """
        Find stations by code, name or city.
        :param query: text such as "Dibrugarh", "Bengaluru" or "GHY"
        :returns: matching stations
        """
        return [
            to_dict(station)
            for station in self.stations.values()
            if matches(query, station.code, station.name, station.city)
        ]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_trains(self, from_station: str, to_station: str, journey_date: str) -> list[dict[str, Any]]:
        """
        Find trains from one station to another that the user can board on a given date.
        :param from_station: boarding station code
        :param to_station: destination station code
        :param journey_date: boarding date, format YYYY-MM-DD
        :returns: trains with departure, arrival, duration and classes, sorted by departure time
        """
        parse_date(journey_date)
        results = []
        for train in self.trains.values():
            try:
                board, alight = self._segment(train, from_station, to_station)
                start = self._start_date(train, board, journey_date)
            except ValueError:
                continue
            change = self._change(train.train_number, start)
            departs = self._event_time(start, board, "departure", change.delay_minutes)
            arrives = self._event_time(start, alight, "arrival", change.delay_minutes)
            results.append(
                {
                    "train_number": train.train_number,
                    "name": train.name,
                    "from_station": from_station,
                    "to_station": to_station,
                    "departure": departs.strftime("%Y-%m-%d %H:%M"),
                    "arrival": arrives.strftime("%Y-%m-%d %H:%M"),
                    "duration_hours": round((arrives - departs) / timedelta(hours=1), 1),
                    "distance_km": alight["distance_km"] - board["distance_km"],
                    "classes": list(train.classes),
                    "delay_minutes": change.delay_minutes,
                    "cancelled": change.cancelled,
                }
            )
        results.sort(key=lambda result: result["departure"])
        return results

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_train_schedule(self, train_number: str) -> dict[str, Any]:
        """
        Get a train's full route, timings and running days.
        :param train_number: the 5-digit train number
        :returns: the train with its stops (arrival, departure, day offset, distance)
        """
        return to_dict(self._train(train_number))

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def check_availability(
        self,
        train_number: str,
        journey_date: str,
        from_station: str,
        to_station: str,
        travel_class: str,
        quota: str = "GN",
    ) -> dict[str, Any]:
        """
        Check seat availability and fare on a train for one date, class and quota.
        :param train_number: the 5-digit train number
        :param journey_date: boarding date, format YYYY-MM-DD
        :param from_station: boarding station code
        :param to_station: destination station code
        :param travel_class: one of 1A, 2A, 3A, SL, CC, 2S
        :param quota: one of GN, TQ, SS, LD
        :returns: status (AVAILABLE-n, RAC-n, WL-n or REGRET), fare per passenger, and whether booking is open
        """
        train = self._train(train_number)
        board, alight = self._segment(train, from_station, to_station)
        start = self._start_date(train, board, journey_date)
        slot = self._slot(train_number, start, travel_class, quota)
        change = self._change(train_number, start)
        try:
            self._check_booking_window(train, board, start, journey_date, travel_class, quota)
            booking_open, reason = True, ""
        except ValueError as error:
            booking_open, reason = False, str(error)
        return {
            "train_number": train_number,
            "journey_date": journey_date,
            "travel_class": travel_class,
            "quota": quota,
            "status": "CANCELLED" if change.cancelled else self._status_text(slot),
            "fare_per_passenger": self._fare(train, board, alight, travel_class, quota),
            "booking_open": booking_open and not change.cancelled,
            "reason": reason,
        }

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_fare(
        self, train_number: str, from_station: str, to_station: str, travel_class: str, quota: str = "GN"
    ) -> int:
        """
        Get the fare per passenger for a journey.
        :param train_number: the 5-digit train number
        :param from_station: boarding station code
        :param to_station: destination station code
        :param travel_class: one of 1A, 2A, 3A, SL, CC, 2S
        :param quota: one of GN, TQ, SS, LD
        :returns: fare per passenger in rupees
        """
        train = self._train(train_number)
        board, alight = self._segment(train, from_station, to_station)
        return self._fare(train, board, alight, travel_class, quota)

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_saved_passengers(self) -> list[dict[str, Any]]:
        """
        List the user's saved passengers.
        :returns: saved passengers with name, age, gender and berth preference
        """
        return [to_dict(passenger) for passenger in self.saved_passengers.values()]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_bookings(self, status: str | None = None) -> list[dict[str, Any]]:
        """
        List the user's train bookings, latest journey first.
        :param status: optional filter: booked, partially_cancelled or cancelled
        :returns: bookings
        """
        selected = [b for b in self.bookings.values() if status is None or b.status == status]
        selected.sort(key=lambda booking: booking.journey_date, reverse=True)
        return [to_dict(booking) for booking in selected]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_pnr_status(self, pnr: str) -> dict[str, Any]:
        """
        Get a booking and the current status of each passenger.
        :param pnr: the 10-digit PNR
        :returns: the booking with passenger statuses, coach and berth
        """
        return to_dict(self._booking(pnr))

    # Write tools -----------------------------------------------------------------
    def _check_booking_window(
        self, train: Train, board: dict, start: date, journey_date: str, travel_class: str, quota: str
    ) -> None:
        departs = self._event_time(start, board, "departure", self._change(train.train_number, start).delay_minutes)
        now = self.now()
        if departs <= now:
            raise ValueError("The train has already left the boarding station")
        days_ahead = (parse_date(journey_date) - now.date()).days
        if days_ahead > ADVANCE_BOOKING_DAYS:
            opens = parse_date(journey_date) - timedelta(days=ADVANCE_BOOKING_DAYS)
            raise ValueError(f"Booking for {journey_date} opens on {opens.isoformat()} (60 days before the journey)")
        if quota == "TQ":
            if travel_class == "1A":
                raise ValueError("Tatkal is not available in 1A")
            opens = datetime.combine(
                parse_date(journey_date) - timedelta(days=1),
                TATKAL_OPENS[travel_class in AC_CLASSES],
                tzinfo=timezone.utc,
            )
            if now < opens:
                raise ValueError(f"Tatkal booking for {journey_date} opens at {opens.strftime('%Y-%m-%d %H:%M')}")

    @staticmethod
    def _check_quota(quota: str, passengers: list[SavedPassenger]) -> None:
        if quota not in QUOTAS:
            raise ValueError(f"Unknown quota {quota}; use one of {', '.join(QUOTAS)}")
        if not passengers:
            raise ValueError("At least one passenger is required")
        if len(passengers) > MAX_PASSENGERS[quota]:
            raise ValueError(f"At most {MAX_PASSENGERS[quota]} passengers can be booked under quota {quota}")
        if quota == "SS":
            for passenger in passengers:
                senior_age = 45 if passenger.gender.lower() == "female" else 60
                if passenger.age < senior_age:
                    raise ValueError(f"{passenger.name} is not eligible for the senior citizen quota")
        if quota == "LD" and any(p.gender.lower() != "female" and p.age >= 12 for p in passengers):
            raise ValueError("The ladies quota allows only women and children under 12")
        for passenger in passengers:
            if passenger.age < 5:
                raise ValueError(
                    f"{passenger.name} is under 5 and travels free without a berth; do not book them as a passenger"
                )

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def book_ticket(
        self,
        train_number: str,
        journey_date: str,
        from_station: str,
        to_station: str,
        travel_class: str,
        passenger_ids: list[str],
        payment: str,
        quota: str = "GN",
    ) -> dict[str, Any]:
        """
        Book a train ticket for saved passengers and pay through PaySetu.
        :param train_number: the 5-digit train number
        :param journey_date: boarding date, format YYYY-MM-DD
        :param from_station: boarding station code
        :param to_station: destination station code
        :param travel_class: one of 1A, 2A, 3A, SL, CC, 2S
        :param passenger_ids: IDs of saved passengers to book (see list_saved_passengers)
        :param payment: PaySetu source_id to pay with
        :param quota: one of GN (general), TQ (Tatkal), SS (senior citizen), LD (ladies)
        :returns: the new booking with its PNR and passenger statuses
        """
        if travel_class not in CLASSES:
            raise ValueError(f"Unknown class {travel_class}; use one of {', '.join(CLASSES)}")
        if len(set(passenger_ids)) != len(passenger_ids):
            raise ValueError("A passenger is listed more than once")
        for passenger_id in passenger_ids:
            if passenger_id not in self.saved_passengers:
                raise ValueError(f"Saved passenger {passenger_id} does not exist")
        passengers = [self.saved_passengers[pid] for pid in passenger_ids]
        self._check_quota(quota, passengers)
        train = self._train(train_number)
        board, alight = self._segment(train, from_station, to_station)
        start = self._start_date(train, board, journey_date)
        if self._change(train_number, start).cancelled:
            raise ValueError(f"Train {train_number} is cancelled on this date")
        self._check_booking_window(train, board, start, journey_date, travel_class, quota)
        slot = self._slot(train_number, start, travel_class, quota)
        fare = self._fare(train, board, alight, travel_class, quota)
        total = fare * len(passengers)
        pnr = str(4_700_000_000 + int(self.next_id("PNR", 6).split("-")[1]))
        snapshot = to_dict(slot)
        allocations = self._allocate(slot, len(passengers))
        try:
            txn_id = self.charge(total, payment, "travel", pnr, merchant="RailMitra")
        except Exception:
            for key, value in snapshot.items():
                setattr(slot, key, value)
            raise
        booking = Booking(
            pnr=pnr,
            train_number=train_number,
            journey_date=journey_date,
            from_station=from_station,
            to_station=to_station,
            travel_class=travel_class,
            quota=quota,
            passengers=[
                {
                    "passenger_id": passenger.passenger_id,
                    "name": passenger.name,
                    "age": passenger.age,
                    "gender": passenger.gender,
                    "fare": fare,
                    "booking_status": status,
                    "current_status": status,
                    "coach": coach,
                    "berth": berth,
                    "berth_type": berth_type,
                }
                for passenger, (status, coach, berth, berth_type) in zip(passengers, allocations)
            ],
            total_fare=total,
            txn_id=txn_id,
            booked_at=self.now_str(),
        )
        self.bookings[pnr] = booking
        return to_dict(booking)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_ticket(self, pnr: str, passenger_ids: list[str]) -> dict[str, Any]:
        """
        Cancel some or all passengers on a booking. The refund goes back to the PaySetu source that paid.
        :param pnr: the 10-digit PNR
        :param passenger_ids: IDs of the passengers to cancel; list every passenger to cancel the whole booking
        :returns: the refund amount and the updated booking
        """
        booking = self._booking(pnr)
        if not passenger_ids:
            raise ValueError("List at least one passenger to cancel")
        by_id = {p["passenger_id"]: p for p in booking.passengers}
        for passenger_id in passenger_ids:
            if passenger_id not in by_id:
                raise ValueError(f"Passenger {passenger_id} is not on PNR {pnr}")
            if by_id[passenger_id]["current_status"] == "CAN":
                raise ValueError(f"Passenger {passenger_id} is already cancelled")
        hours = self.hours_until(self._departure_for(booking))
        if hours <= 0:
            raise ValueError("The train has already left; this ticket can no longer be cancelled")
        refund = 0
        for passenger_id in passenger_ids:
            passenger = by_id[passenger_id]
            refund += self._cancellation_refund(booking, passenger, hours)
            passenger["current_status"] = "CAN"
        self._refund_booking(booking, refund)
        self._update_booking_status(booking)
        return {"refund": refund, "booking": to_dict(booking)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_saved_passenger(self, name: str, age: int, gender: str, berth_preference: str = "none") -> str:
        """
        Save a passenger for future bookings.
        :param name: full name as on ID proof
        :param age: age in years
        :param gender: Male, Female or Other
        :param berth_preference: one of LB, MB, UB, SL, SU, none
        :returns: the passenger ID
        """
        if berth_preference not in ("LB", "MB", "UB", "SL", "SU", "none"):
            raise ValueError("berth_preference must be one of LB, MB, UB, SL, SU, none")
        passenger = SavedPassenger(
            passenger_id=self.next_id("RM-PAX", 3),
            name=name,
            age=age,
            gender=gender,
            berth_preference=berth_preference,
        )
        self.saved_passengers[passenger.passenger_id] = passenger
        return passenger.passenger_id

    # Environment events -------------------------------------------------------
    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_passenger_status(
        self, pnr: str, passenger_id: str, status: str, coach: str = "", berth: int = 0
    ) -> dict[str, Any]:
        """
        Move a passenger's status, e.g. from WL-3 to RAC-1 or to CNF with a coach and berth.
        :param pnr: the PNR
        :param passenger_id: the passenger ID
        :param status: new status such as "RAC-1" or "CNF"
        :param coach: coach for a confirmed berth, e.g. "B2"
        :param berth: berth number for a confirmed berth
        :returns: the updated booking
        """
        booking = self._booking(pnr)
        for passenger in booking.passengers:
            if passenger["passenger_id"] == passenger_id:
                passenger["current_status"] = status
                if status == "CNF":
                    pattern = BERTH_PATTERN[booking.travel_class]
                    passenger.update(coach=coach, berth=berth, berth_type=pattern[(berth - 1) % len(pattern)])
                return to_dict(booking)
        raise ValueError(f"Passenger {passenger_id} is not on PNR {pnr}")

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def prepare_chart(self, train_number: str, start_date: str) -> list[str]:
        """
        Prepare the chart for one run of a train. Passengers still fully waitlisted are cancelled
        and refunded their fare minus 60 rupees.
        :param train_number: the train number
        :param start_date: date the train leaves its origin, format YYYY-MM-DD
        :returns: PNRs that were charted
        """
        charted = []
        for booking in self.bookings.values():
            if booking.train_number != train_number or booking.chart_prepared:
                continue
            board = self._stop(self._train(train_number), booking.from_station)
            origin = parse_date(booking.journey_date) - timedelta(days=board["day_offset"])
            if origin.isoformat() != start_date:
                continue
            booking.chart_prepared = True
            refund = 0
            for passenger in booking.passengers:
                if passenger["current_status"].startswith("WL"):
                    refund += max(passenger["fare"] - WAITLIST_CLERKAGE, 0)
                    passenger["current_status"] = "CAN"
            self._refund_booking(booking, refund)
            self._update_booking_status(booking)
            charted.append(booking.pnr)
        return charted

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def delay_train(self, train_number: str, start_date: str, delay_minutes: int) -> None:
        """
        Delay one run of a train; every stop shifts by the delay.
        :param train_number: the train number
        :param start_date: date the train leaves its origin, format YYYY-MM-DD
        :param delay_minutes: delay in minutes
        """
        self._train(train_number)
        key = _run_key(train_number, parse_date(start_date).isoformat())
        change = self.run_changes.setdefault(key, TrainRunChange())
        change.delay_minutes = delay_minutes

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def cancel_train_run(self, train_number: str, start_date: str) -> list[str]:
        """
        Cancel one run of a train. Every booking on it is cancelled with a full refund.
        :param train_number: the train number
        :param start_date: date the train leaves its origin, format YYYY-MM-DD
        :returns: PNRs that were cancelled
        """
        train = self._train(train_number)
        key = _run_key(train_number, parse_date(start_date).isoformat())
        self.run_changes.setdefault(key, TrainRunChange()).cancelled = True
        cancelled = []
        for booking in self.bookings.values():
            if booking.train_number != train_number or booking.status == "cancelled":
                continue
            board = self._stop(train, booking.from_station)
            origin = parse_date(booking.journey_date) - timedelta(days=board["day_offset"])
            if origin.isoformat() != start_date:
                continue
            refund = sum(p["fare"] for p in booking.passengers if p["current_status"] != "CAN")
            for passenger in booking.passengers:
                passenger["current_status"] = "CAN"
            self._refund_booking(booking, refund)
            self._update_booking_status(booking)
            cancelled.append(booking.pnr)
        return cancelled
