"""SafarHub: flights, hotels and packages, modelled on MakeMyTrip / Goibibo / Yatra.

Schema: app_schemas.md section 3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
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
    round_rupees,
    to_dict,
)

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
FARE_FAMILIES = ("saver", "flexi")
TRAVELLER_TYPES = ("adult", "child")
PACKAGE_CHILD_AGES = range(5, 12)


@dataclass
class Airport:
    code: str
    city: str
    name: str


@dataclass
class FlightSchedule:
    flight_id: str
    airline: str
    flight_number: str
    from_airport: str
    to_airport: str
    departure_time: str
    arrival_time: str
    days: list[str]
    fares: dict[str, dict[str, Any]]
    seats: int
    arrival_day_offset: int = 0
    stops: list[str] = field(default_factory=list)


@dataclass
class FarePricing:
    rule_id: str
    start_date: str
    end_date: str
    multiplier: float
    label: str = ""
    festival: bool = False


@dataclass
class FlightChange:
    departure_time: str | None = None
    arrival_time: str | None = None
    cancelled: bool = False


@dataclass
class Hotel:
    hotel_id: str
    name: str
    city: str
    area: str
    star_rating: int
    guest_rating: float
    room_types: list[dict[str, Any]]
    tags: list[str] = field(default_factory=list)
    check_in_time: str = "14:00"
    check_out_time: str = "11:00"


@dataclass
class Package:
    package_id: str
    category: str
    title: str
    destination: str
    nights: int
    inclusions: list[str]
    available_start_dates: list[str]
    price_per_adult: int
    price_per_child: int
    slots_left: dict[str, int]
    cancellation: list[dict[str, int]]
    description: str = ""


@dataclass
class SavedTraveller:
    traveller_id: str
    name: str
    date_of_birth: str
    gender: str
    type: str


@dataclass
class TravelBooking:
    booking_id: str
    type: str
    item_id: str
    details: dict[str, Any]
    traveller_ids: list[str]
    amount: int
    txn_id: str
    booked_at: str
    status: str = "confirmed"
    refunded_amount: int = 0


def _age_on(date_of_birth: str, on: date) -> int:
    born = parse_date(date_of_birth)
    return on.year - born.year - ((on.month, on.day) < (born.month, born.day))


def _at(day: date, clock: str) -> datetime:
    hours, minutes = (int(part) for part in clock.split(":"))
    return datetime(day.year, day.month, day.day, hours, minutes, tzinfo=timezone.utc)


class SafarHubApp(BharatApp):
    """
    SafarHub books domestic flights, hotels, and holiday packages (pilgrimage and relaxation).

    Notes:
        - Airports are named by IATA code, e.g. "BLR" (Bengaluru), "DIB" (Dibrugarh), "GAU" (Guwahati).
        - Flights have two fare families: "saver" and "flexi". Each has its own baggage, cancellation fee
          and change fee. Prices change by date; festival dates cost more.
        - Saver fares on festival dates are non-refundable. Otherwise a cancelled flight refunds the amount
          minus the cancellation fee per traveller.
        - Children (2 and above) pay the adult airfare. Infants are not supported.
        - Hotels: cancellation is free up to the room's free_cancellation_days before check-in;
          later cancellations are charged the first night.
        - Packages: children aged 5 to 11 pay the child price, under 5 travel free; refunds follow the
          package's own cancellation table.
        - Dates use YYYY-MM-DD and times are local (IST). Amounts are whole rupees.
    """

    def __init__(self, name: str | None = "SafarHub") -> None:
        super().__init__(name)
        self.airports: dict[str, Airport] = {}
        self.flights: dict[str, FlightSchedule] = {}
        self.fare_pricing: dict[str, FarePricing] = {}
        self.flight_sales: dict[str, int] = {}
        self.flight_changes: dict[str, FlightChange] = {}
        self.hotels: dict[str, Hotel] = {}
        self.room_sales: dict[str, int] = {}
        self.packages: dict[str, Package] = {}
        self.saved_travellers: dict[str, SavedTraveller] = {}
        self.bookings: dict[str, TravelBooking] = {}

    # State -----------------------------------------------------------------
    def get_state(self) -> dict[str, Any]:
        return {
            **self.base_state(),
            "airports": dump_records(self.airports),
            "flights": dump_records(self.flights),
            "fare_pricing": dump_records(self.fare_pricing),
            "flight_sales": dict(self.flight_sales),
            "flight_changes": dump_records(self.flight_changes),
            "hotels": dump_records(self.hotels),
            "room_sales": dict(self.room_sales),
            "packages": dump_records(self.packages),
            "saved_travellers": dump_records(self.saved_travellers),
            "bookings": dump_records(self.bookings),
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self.load_base_state(state_dict)
        self.airports = load_records(Airport, state_dict.get("airports", {}))
        self.flights = load_records(FlightSchedule, state_dict.get("flights", {}))
        self.fare_pricing = load_records(FarePricing, state_dict.get("fare_pricing", {}))
        self.flight_sales = dict(state_dict.get("flight_sales", {}))
        self.flight_changes = load_records(FlightChange, state_dict.get("flight_changes", {}))
        self.hotels = load_records(Hotel, state_dict.get("hotels", {}))
        self.room_sales = dict(state_dict.get("room_sales", {}))
        self.packages = load_records(Package, state_dict.get("packages", {}))
        self.saved_travellers = load_records(SavedTraveller, state_dict.get("saved_travellers", {}))
        self.bookings = load_records(TravelBooking, state_dict.get("bookings", {}))

    # Flight helpers ------------------------------------------------------------
    def _flight(self, flight_id: str) -> FlightSchedule:
        if flight_id not in self.flights:
            raise ValueError(f"Flight {flight_id} does not exist")
        return self.flights[flight_id]

    def _pricing_rules(self, day: date) -> list[FarePricing]:
        return [
            rule
            for rule in self.fare_pricing.values()
            if parse_date(rule.start_date) <= day <= parse_date(rule.end_date)
        ]

    def _multiplier(self, day: date) -> float:
        return max((rule.multiplier for rule in self._pricing_rules(day)), default=1.0)

    def _is_festival(self, day: date) -> bool:
        return any(rule.festival for rule in self._pricing_rules(day))

    def _price_per_traveller(self, flight: FlightSchedule, day: date, fare_family: str) -> int:
        if fare_family not in flight.fares:
            raise ValueError(f"Fare family must be one of {', '.join(flight.fares)}")
        return round_rupees(flight.fares[fare_family]["base_price"] * self._multiplier(day))

    def _refundable(self, flight: FlightSchedule, day: date, fare_family: str) -> bool:
        if not flight.fares[fare_family].get("refundable", True):
            return False
        return not (fare_family == "saver" and self._is_festival(day))

    def _flight_times(self, flight: FlightSchedule, day: date) -> tuple[datetime, datetime, bool]:
        change = self.flight_changes.get(f"{flight.flight_id}|{day.isoformat()}", FlightChange())
        departs = _at(day, change.departure_time or flight.departure_time)
        arrives = _at(day + timedelta(days=flight.arrival_day_offset), change.arrival_time or flight.arrival_time)
        return departs, arrives, change.cancelled

    def _check_operates(self, flight: FlightSchedule, day: date) -> None:
        if WEEKDAYS[day.weekday()] not in flight.days:
            raise ValueError(f"Flight {flight.flight_number} does not operate on {day.isoformat()}")

    def _seats_left(self, flight: FlightSchedule, day: date) -> int:
        return flight.seats - self.flight_sales.get(f"{flight.flight_id}|{day.isoformat()}", 0)

    # Hotel and package helpers ---------------------------------------------------
    def _hotel(self, hotel_id: str) -> Hotel:
        if hotel_id not in self.hotels:
            raise ValueError(f"Hotel {hotel_id} does not exist")
        return self.hotels[hotel_id]

    @staticmethod
    def _room(hotel: Hotel, room_type: str) -> dict[str, Any]:
        for room in hotel.room_types:
            if room["room_type"] == room_type:
                return room
        raise ValueError(f"Hotel {hotel.hotel_id} has no room type '{room_type}'")

    @staticmethod
    def _nights(check_in: str, check_out: str) -> list[date]:
        start, end = parse_date(check_in), parse_date(check_out)
        if end <= start:
            raise ValueError("check_out must be after check_in")
        return [start + timedelta(days=offset) for offset in range((end - start).days)]

    def _rooms_free(self, hotel: Hotel, room: dict[str, Any], nights: list[date]) -> int:
        return min(
            room["rooms_total"] - self.room_sales.get(f"{hotel.hotel_id}|{room['room_type']}|{night}", 0)
            for night in nights
        )

    def _package(self, package_id: str) -> Package:
        if package_id not in self.packages:
            raise ValueError(f"Package {package_id} does not exist")
        return self.packages[package_id]

    def _travellers(self, traveller_ids: list[str]) -> list[SavedTraveller]:
        if not traveller_ids:
            raise ValueError("At least one traveller is required")
        if len(set(traveller_ids)) != len(traveller_ids):
            raise ValueError("A traveller is listed more than once")
        for traveller_id in traveller_ids:
            if traveller_id not in self.saved_travellers:
                raise ValueError(f"Saved traveller {traveller_id} does not exist")
        return [self.saved_travellers[traveller_id] for traveller_id in traveller_ids]

    def _booking(self, booking_id: str) -> TravelBooking:
        if booking_id not in self.bookings:
            raise ValueError(f"Booking {booking_id} does not exist")
        return self.bookings[booking_id]

    def _record_booking(
        self, kind: str, item_id: str, details: dict, traveller_ids: list[str], amount: int, payment: str
    ) -> TravelBooking:
        booking_id = self.next_id("SH-BK")
        txn_id = self.charge(amount, payment, "travel", booking_id, merchant="SafarHub")
        booking = TravelBooking(
            booking_id=booking_id,
            type=kind,
            item_id=item_id,
            details=details,
            traveller_ids=list(traveller_ids),
            amount=amount,
            txn_id=txn_id,
            booked_at=self.now_str(),
        )
        self.bookings[booking_id] = booking
        return booking

    def _close_booking(self, booking: TravelBooking, refund: int) -> int:
        if refund > 0:
            self.refund(booking.txn_id, refund)
            booking.refunded_amount += refund
        booking.status = "cancelled"
        return refund

    # Read tools --------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_flights(
        self,
        from_airport: str,
        to_airport: str,
        date: str,
        adults: int,
        children: int = 0,
        sort_by: str = "price",
        non_stop_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Search flights for one date.
        :param from_airport: departure airport code, e.g. "BLR"
        :param to_airport: arrival airport code, e.g. "DIB"
        :param date: departure date, format YYYY-MM-DD
        :param adults: number of adults
        :param children: number of children (they pay the adult fare)
        :param sort_by: "price", "departure" or "duration"
        :param non_stop_only: show only flights without stops
        :returns: flights with times, stops, seats left, and saver and flexi prices per traveller and in total
        """
        day = parse_date(date)
        travellers = adults + children
        if travellers <= 0:
            raise ValueError("At least one traveller is required")
        results = []
        for flight in self.flights.values():
            if flight.from_airport != from_airport or flight.to_airport != to_airport:
                continue
            if WEEKDAYS[day.weekday()] not in flight.days or (non_stop_only and flight.stops):
                continue
            departs, arrives, cancelled = self._flight_times(flight, day)
            if cancelled or departs <= self.now():
                continue
            fares = {
                family: {
                    "price_per_traveller": self._price_per_traveller(flight, day, family),
                    "total": self._price_per_traveller(flight, day, family) * travellers,
                    "refundable": self._refundable(flight, day, family),
                }
                for family in flight.fares
            }
            results.append(
                {
                    "flight_id": flight.flight_id,
                    "airline": flight.airline,
                    "flight_number": flight.flight_number,
                    "departure": departs.strftime("%Y-%m-%d %H:%M"),
                    "arrival": arrives.strftime("%Y-%m-%d %H:%M"),
                    "duration_minutes": int((arrives - departs) / timedelta(minutes=1)),
                    "stops": list(flight.stops),
                    "seats_left": self._seats_left(flight, day),
                    "fares": fares,
                }
            )
        keys = {
            "price": lambda r: min(f["price_per_traveller"] for f in r["fares"].values()),
            "departure": lambda r: r["departure"],
            "duration": lambda r: r["duration_minutes"],
        }
        if sort_by not in keys:
            raise ValueError("sort_by must be price, departure or duration")
        results.sort(key=lambda r: (keys[sort_by](r), r["flight_id"]))
        return results

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_flight_fare(self, flight_id: str, date: str, fare_family: str) -> dict[str, Any]:
        """
        Get the fare rules and price of one flight on one date.
        :param flight_id: the flight ID from search_flights
        :param date: departure date, format YYYY-MM-DD
        :param fare_family: "saver" or "flexi"
        :returns: price per traveller, baggage, fees, and whether it is refundable on that date
        """
        flight = self._flight(flight_id)
        day = parse_date(date)
        self._check_operates(flight, day)
        rules = dict(flight.fares[fare_family]) if fare_family in flight.fares else None
        if rules is None:
            raise ValueError(f"Fare family must be one of {', '.join(flight.fares)}")
        rules.pop("base_price", None)
        return {
            "flight_id": flight_id,
            "date": date,
            "fare_family": fare_family,
            "price_per_traveller": self._price_per_traveller(flight, day, fare_family),
            **rules,
            "refundable": self._refundable(flight, day, fare_family),
            "festival_pricing": self._is_festival(day),
        }

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        adults: int,
        children: int = 0,
        tags: list[str] | None = None,
        sort_by: str = "price",
    ) -> list[dict[str, Any]]:
        """
        Search hotels in a city for a stay.
        :param city: city name, e.g. "Madikeri"
        :param check_in: check-in date, format YYYY-MM-DD
        :param check_out: check-out date, format YYYY-MM-DD
        :param adults: number of adults
        :param children: number of children
        :param tags: only hotels having all these tags, e.g. ["pool", "family_friendly"]
        :param sort_by: "price" or "rating"
        :returns: hotels with each available room type, the rooms needed for the guests, and the stay price
        """
        nights = self._nights(check_in, check_out)
        results = []
        for hotel in self.hotels.values():
            if not matches(city, hotel.city) or not set(tags or []).issubset(hotel.tags):
                continue
            options = []
            for room in hotel.room_types:
                if children and not room["max_children"]:
                    continue
                rooms_needed = max(
                    1,
                    math.ceil(adults / room["max_adults"]),
                    math.ceil(children / room["max_children"]) if children else 0,
                )
                if self._rooms_free(hotel, room, nights) < rooms_needed:
                    continue
                options.append(
                    {
                        "room_type": room["room_type"],
                        "meal_plan": room["meal_plan"],
                        "price_per_night": room["price_per_night"],
                        "rooms_needed": rooms_needed,
                        "stay_total": room["price_per_night"] * len(nights) * rooms_needed,
                        "free_cancellation_days": room["free_cancellation_days"],
                    }
                )
            if options:
                results.append(
                    {
                        "hotel_id": hotel.hotel_id,
                        "name": hotel.name,
                        "area": hotel.area,
                        "star_rating": hotel.star_rating,
                        "guest_rating": hotel.guest_rating,
                        "tags": list(hotel.tags),
                        "rooms": sorted(options, key=lambda option: option["stay_total"]),
                    }
                )
        if sort_by == "price":
            results.sort(key=lambda r: (r["rooms"][0]["stay_total"], r["hotel_id"]))
        elif sort_by == "rating":
            results.sort(key=lambda r: (-r["guest_rating"], r["hotel_id"]))
        else:
            raise ValueError("sort_by must be price or rating")
        return results

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_hotel_details(self, hotel_id: str) -> dict[str, Any]:
        """
        Get a hotel's details, tags and all room types.
        :param hotel_id: the hotel ID
        :returns: the hotel
        """
        return to_dict(self._hotel(hotel_id))

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_packages(
        self,
        category: str | None = None,
        destination: str | None = None,
        start_date_from: str | None = None,
        start_date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search holiday packages.
        :param category: "pilgrimage" or "relaxation"
        :param destination: text matched against the destination and title
        :param start_date_from: only packages with a start date on or after this date, format YYYY-MM-DD
        :param start_date_to: only packages with a start date on or before this date, format YYYY-MM-DD
        :returns: packages with their matching start dates and slots left
        """
        low = parse_date(start_date_from) if start_date_from else None
        high = parse_date(start_date_to) if start_date_to else None
        results = []
        for package in self.packages.values():
            if category and package.category != category:
                continue
            if not matches(destination, package.destination, package.title):
                continue
            dates = [
                start
                for start in package.available_start_dates
                if (low is None or parse_date(start) >= low)
                and (high is None or parse_date(start) <= high)
                and parse_date(start) > self.today()
            ]
            if dates:
                results.append(
                    {
                        "package_id": package.package_id,
                        "category": package.category,
                        "title": package.title,
                        "destination": package.destination,
                        "nights": package.nights,
                        "price_per_adult": package.price_per_adult,
                        "price_per_child": package.price_per_child,
                        "start_dates": {start: package.slots_left.get(start, 0) for start in dates},
                    }
                )
        results.sort(key=lambda r: (r["price_per_adult"], r["package_id"]))
        return results

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_package_details(self, package_id: str) -> dict[str, Any]:
        """
        Get a package's inclusions, start dates, slots and cancellation table.
        :param package_id: the package ID
        :returns: the package
        """
        return to_dict(self._package(package_id))

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_saved_travellers(self) -> list[dict[str, Any]]:
        """
        List saved travellers.
        :returns: travellers with name, date of birth, gender and type (adult or child)
        """
        return [to_dict(traveller) for traveller in self.saved_travellers.values()]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_bookings(self, type: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        """
        List bookings, newest first.
        :param type: "flight", "hotel" or "package"
        :param status: "confirmed", "cancelled" or "completed"
        :returns: bookings
        """
        selected = [
            booking
            for booking in self.bookings.values()
            if (type is None or booking.type == type) and (status is None or booking.status == status)
        ]
        selected.sort(key=lambda booking: (booking.booked_at, booking.booking_id), reverse=True)
        return [to_dict(booking) for booking in selected]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_booking(self, booking_id: str) -> dict[str, Any]:
        """
        Get one booking.
        :param booking_id: the booking ID
        :returns: the booking
        """
        return to_dict(self._booking(booking_id))

    # Write tools -----------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def book_flight(
        self, flight_id: str, date: str, fare_family: str, traveller_ids: list[str], payment: str
    ) -> dict[str, Any]:
        """
        Book a flight for saved travellers and pay through PaySetu.
        :param flight_id: the flight ID from search_flights
        :param date: departure date, format YYYY-MM-DD
        :param fare_family: "saver" or "flexi"
        :param traveller_ids: IDs of saved travellers (see list_saved_travellers)
        :param payment: PaySetu source_id to pay with
        :returns: the new booking
        """
        flight = self._flight(flight_id)
        day = parse_date(date)
        self._check_operates(flight, day)
        travellers = self._travellers(traveller_ids)
        departs, arrives, cancelled = self._flight_times(flight, day)
        if cancelled:
            raise ValueError(f"Flight {flight.flight_number} is cancelled on {date}")
        if departs <= self.now():
            raise ValueError("This flight has already departed")
        if self._seats_left(flight, day) < len(travellers):
            raise ValueError(f"Only {self._seats_left(flight, day)} seats left on this flight")
        price = self._price_per_traveller(flight, day, fare_family)
        details = {
            "date": date,
            "fare_family": fare_family,
            "flight_number": flight.flight_number,
            "airline": flight.airline,
            "from_airport": flight.from_airport,
            "to_airport": flight.to_airport,
            "departure": departs.strftime("%Y-%m-%d %H:%M"),
            "arrival": arrives.strftime("%Y-%m-%d %H:%M"),
            "price_per_traveller": price,
            "refundable": self._refundable(flight, day, fare_family),
            "cancellation_fee_per_traveller": flight.fares[fare_family]["cancellation_fee"],
        }
        booking = self._record_booking("flight", flight_id, details, traveller_ids, price * len(travellers), payment)
        key = f"{flight_id}|{date}"
        self.flight_sales[key] = self.flight_sales.get(key, 0) + len(travellers)
        return to_dict(booking)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def book_hotel(
        self,
        hotel_id: str,
        room_type: str,
        check_in: str,
        check_out: str,
        rooms: int,
        adults: int,
        children: int,
        payment: str,
    ) -> dict[str, Any]:
        """
        Book hotel rooms and pay through PaySetu.
        :param hotel_id: the hotel ID
        :param room_type: room type name exactly as listed by the hotel
        :param check_in: check-in date, format YYYY-MM-DD
        :param check_out: check-out date, format YYYY-MM-DD
        :param rooms: number of rooms
        :param adults: number of adults
        :param children: number of children
        :param payment: PaySetu source_id to pay with
        :returns: the new booking
        """
        hotel = self._hotel(hotel_id)
        room = self._room(hotel, room_type)
        nights = self._nights(check_in, check_out)
        if nights[0] < self.today():
            raise ValueError("check_in cannot be in the past")
        if rooms <= 0 or adults <= 0 or children < 0:
            raise ValueError("rooms and adults must be at least 1, children at least 0")
        if rooms * room["max_adults"] < adults or rooms * room["max_children"] < children:
            raise ValueError(
                f"{rooms} x {room_type} fits at most {rooms * room['max_adults']} adults and "
                f"{rooms * room['max_children']} children"
            )
        if self._rooms_free(hotel, room, nights) < rooms:
            raise ValueError(f"Not enough {room_type} rooms free for these dates")
        amount = room["price_per_night"] * len(nights) * rooms
        details = {
            "hotel_name": hotel.name,
            "city": hotel.city,
            "room_type": room_type,
            "meal_plan": room["meal_plan"],
            "check_in": check_in,
            "check_out": check_out,
            "rooms": rooms,
            "adults": adults,
            "children": children,
            "price_per_night": room["price_per_night"],
            "free_cancellation_days": room["free_cancellation_days"],
        }
        booking = self._record_booking("hotel", hotel_id, details, [], amount, payment)
        for night in nights:
            key = f"{hotel_id}|{room_type}|{night}"
            self.room_sales[key] = self.room_sales.get(key, 0) + rooms
        return to_dict(booking)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def book_package(self, package_id: str, start_date: str, traveller_ids: list[str], payment: str) -> dict[str, Any]:
        """
        Book a holiday package for saved travellers and pay through PaySetu.
        :param package_id: the package ID
        :param start_date: one of the package's available start dates, format YYYY-MM-DD
        :param traveller_ids: IDs of saved travellers (see list_saved_travellers)
        :param payment: PaySetu source_id to pay with
        :returns: the new booking
        """
        package = self._package(package_id)
        if start_date not in package.available_start_dates:
            raise ValueError(f"{start_date} is not an available start date for this package")
        start = parse_date(start_date)
        if start <= self.today():
            raise ValueError("The package start date must be in the future")
        travellers = self._travellers(traveller_ids)
        ages = [_age_on(traveller.date_of_birth, start) for traveller in travellers]
        paying = [age for age in ages if age >= 5]
        if package.slots_left.get(start_date, 0) < len(paying):
            raise ValueError(f"Only {package.slots_left.get(start_date, 0)} slots left on {start_date}")
        amount = sum(
            package.price_per_child if age in PACKAGE_CHILD_AGES else package.price_per_adult for age in paying
        )
        details = {
            "title": package.title,
            "category": package.category,
            "start_date": start_date,
            "end_date": (start + timedelta(days=package.nights)).isoformat(),
            "nights": package.nights,
            "slots_used": len(paying),
        }
        booking = self._record_booking("package", package_id, details, traveller_ids, amount, payment)
        package.slots_left[start_date] -= len(paying)
        return to_dict(booking)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_booking(self, booking_id: str) -> dict[str, Any]:
        """
        Cancel a booking. The refund, if any, goes back to the PaySetu source that paid.
        :param booking_id: the booking ID
        :returns: the refund amount and the updated booking
        """
        booking = self._booking(booking_id)
        if booking.status != "confirmed":
            raise ValueError(f"Booking {booking_id} is {booking.status}")
        details = booking.details
        if booking.type == "flight":
            flight = self._flight(booking.item_id)
            day = parse_date(details["date"])
            departs, _, _ = self._flight_times(flight, day)
            if departs <= self.now():
                raise ValueError("The flight has already departed")
            fee = details["cancellation_fee_per_traveller"] * len(booking.traveller_ids)
            refund = max(booking.amount - fee, 0) if details["refundable"] else 0
            self.flight_sales[f"{flight.flight_id}|{details['date']}"] -= len(booking.traveller_ids)
        elif booking.type == "hotel":
            check_in = parse_date(details["check_in"])
            if check_in <= self.today():
                raise ValueError("A stay cannot be cancelled on or after the check-in date")
            if (check_in - self.today()).days >= details["free_cancellation_days"]:
                refund = booking.amount
            else:
                refund = booking.amount - details["price_per_night"] * details["rooms"]
            for night in self._nights(details["check_in"], details["check_out"]):
                self.room_sales[f"{booking.item_id}|{details['room_type']}|{night}"] -= details["rooms"]
        else:
            start = parse_date(details["start_date"])
            if start <= self.today():
                raise ValueError("A package cannot be cancelled on or after its start date")
            days_before = (start - self.today()).days
            percent = next(
                (
                    rule["refund_percent"]
                    for rule in sorted(self._package(booking.item_id).cancellation, key=lambda r: -r["days_before"])
                    if days_before >= rule["days_before"]
                ),
                0,
            )
            refund = percent_of(booking.amount, percent)
            self._package(booking.item_id).slots_left[details["start_date"]] += details["slots_used"]
        self._close_booking(booking, refund)
        return {"refund": refund, "booking": to_dict(booking)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_saved_traveller(self, name: str, date_of_birth: str, gender: str, type: str) -> str:
        """
        Save a traveller for future bookings.
        :param name: full name as on ID proof
        :param date_of_birth: format YYYY-MM-DD
        :param gender: Male, Female or Other
        :param type: "adult" or "child"
        :returns: the traveller ID
        """
        parse_date(date_of_birth)
        if type not in TRAVELLER_TYPES:
            raise ValueError("type must be adult or child")
        traveller = SavedTraveller(
            traveller_id=self.next_id("SH-TRV", 3),
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
            type=type,
        )
        self.saved_travellers[traveller.traveller_id] = traveller
        return traveller.traveller_id

    # Environment events -------------------------------------------------------
    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def reschedule_flight(self, flight_id: str, date: str, departure_time: str, arrival_time: str) -> None:
        """
        Change a flight's times on one date. Bookings stay confirmed.
        :param flight_id: the flight ID
        :param date: departure date, format YYYY-MM-DD
        :param departure_time: new departure time, HH:MM
        :param arrival_time: new arrival time, HH:MM
        """
        self._check_operates(self._flight(flight_id), parse_date(date))
        change = self.flight_changes.setdefault(f"{flight_id}|{date}", FlightChange())
        change.departure_time, change.arrival_time = departure_time, arrival_time
        for booking in self.bookings.values():
            if booking.type == "flight" and booking.item_id == flight_id and booking.details["date"] == date:
                departs, arrives, _ = self._flight_times(self._flight(flight_id), parse_date(date))
                booking.details["departure"] = departs.strftime("%Y-%m-%d %H:%M")
                booking.details["arrival"] = arrives.strftime("%Y-%m-%d %H:%M")

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def cancel_flight(self, flight_id: str, date: str) -> list[str]:
        """
        The airline cancels a flight on one date. Every booking on it is cancelled with a full refund.
        :param flight_id: the flight ID
        :param date: departure date, format YYYY-MM-DD
        :returns: booking IDs that were cancelled
        """
        self._check_operates(self._flight(flight_id), parse_date(date))
        self.flight_changes.setdefault(f"{flight_id}|{date}", FlightChange()).cancelled = True
        cancelled = []
        for booking in self.bookings.values():
            if (
                booking.type == "flight"
                and booking.item_id == flight_id
                and booking.details["date"] == date
                and booking.status == "confirmed"
            ):
                self._close_booking(booking, booking.amount)
                cancelled.append(booking.booking_id)
        return cancelled

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_fare_pricing(
        self, rule_id: str, start_date: str, end_date: str, multiplier: float, label: str = "", festival: bool = False
    ) -> None:
        """
        Add or replace a date-range price multiplier for all flights.
        :param rule_id: ID of the pricing rule
        :param start_date: first date the rule applies, format YYYY-MM-DD
        :param end_date: last date the rule applies, format YYYY-MM-DD
        :param multiplier: price multiplier, e.g. 1.4
        :param label: human-readable reason, e.g. "Magh Bihu week"
        :param festival: whether these are festival dates (saver fares become non-refundable)
        """
        parse_date(start_date), parse_date(end_date)
        self.fare_pricing[rule_id] = FarePricing(rule_id, start_date, end_date, multiplier, label, festival)

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_package_slots(self, package_id: str, start_date: str, slots: int) -> None:
        """
        Set the remaining slots of a package on one start date.
        :param package_id: the package ID
        :param start_date: the start date, format YYYY-MM-DD
        :param slots: remaining slots
        """
        package = self._package(package_id)
        if start_date not in package.available_start_dates:
            raise ValueError(f"{start_date} is not a start date of {package_id}")
        package.slots_left[start_date] = slots
