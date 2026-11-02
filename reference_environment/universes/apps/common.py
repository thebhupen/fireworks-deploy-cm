"""Conventions shared by every Bharat universe app.

See ``universes/blr_pranjal_01/app_schemas.md`` section 0. In short:

- Times are IST wall-clock values written in ARE's ``YYYY-MM-DD HH:MM:SS``
  format and stored as if they were UTC, so they line up with ARE's own
  Calendar and Email apps.
- Money is integer rupees. Percentages round half up.
- Runtime IDs come from per-app counters kept in state, so a replayed
  scenario creates the same IDs.
- Apps that take money reach PaySetu through ARE's protocol mechanism under
  ``BharatProtocol.PAYMENT``. ARE's environment does not restrict protocol
  keys, so no change to ARE is needed.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

from are.simulation.apps.app import App

if TYPE_CHECKING:
    from .paysetu import PaySetuApp

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
COD = "cod"


ADDRESS_LABELS = ("home", "office", "brother", "in_laws", "other")


@dataclasses.dataclass
class Address:
    address_id: str
    label: str
    line1: str
    area: str
    city: str
    pincode: str
    phone: str


class BharatProtocol(Enum):
    PAYMENT = "PAYMENT"


def parse_datetime(value: str) -> datetime:
    """Parse ``YYYY-MM-DD HH:MM:SS`` as a wall-clock value in the UTC frame."""
    try:
        return datetime.strptime(value, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError(f"Invalid datetime '{value}', expected format YYYY-MM-DD HH:MM:SS") from error


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError as error:
        raise ValueError(f"Invalid date '{value}', expected format YYYY-MM-DD") from error


def format_datetime(moment: datetime) -> str:
    return moment.strftime(DATETIME_FORMAT)


def epoch_to_datetime(epoch: float) -> datetime:
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def datetime_to_epoch(moment: datetime) -> float:
    return moment.timestamp()


def round_rupees(amount: float | Decimal) -> int:
    """Round to whole rupees, half up (0.5 goes up)."""
    return int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def percent_of(amount: int, percent: float) -> int:
    return round_rupees(Decimal(amount) * Decimal(str(percent)) / Decimal(100))


def round_to_nearest(amount: float, step: int) -> int:
    return round_rupees(Decimal(str(amount)) / Decimal(step)) * step


def to_dict(record: Any) -> dict[str, Any]:
    return dataclasses.asdict(record)


def load_records(record_type: type, raw: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {key: record_type(**value) for key, value in raw.items()}


def dump_records(records: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {key: to_dict(value) for key, value in records.items()}


def page(items: list[Any], offset: int, limit: int) -> dict[str, Any]:
    if offset < 0 or limit <= 0:
        raise ValueError("offset must be >= 0 and limit must be > 0")
    return {
        "items": items[offset : offset + limit],
        "total": len(items),
        "offset": offset,
        "limit": limit,
    }


def matches(query: str | None, *texts: str | None) -> bool:
    if not query:
        return True
    needle = query.casefold()
    return any(needle in (text or "").casefold() for text in texts)


class BharatApp(App):
    """Base class with the clock, ID and payment helpers every app shares."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self.id_counters: dict[str, int] = {}
        self.payment_app: PaySetuApp | None = None

    def reset(self) -> None:
        """Clear all state but keep the PaySetu connection made by the environment."""
        payment_app = self.payment_app
        App.reset(self)
        self.payment_app = payment_app

    # Clock ---------------------------------------------------------------
    def now(self) -> datetime:
        return epoch_to_datetime(self.time_manager.time())

    def now_str(self) -> str:
        return format_datetime(self.now())

    def today(self) -> date:
        return self.now().date()

    def hours_until(self, moment: datetime) -> float:
        return (moment - self.now()) / timedelta(hours=1)

    # IDs -----------------------------------------------------------------
    def next_id(self, prefix: str, width: int = 4) -> str:
        counter = self.id_counters.get(prefix, 0) + 1
        self.id_counters[prefix] = counter
        return f"{prefix}-{counter:0{width}d}"

    # Payments ------------------------------------------------------------
    def connect_to_protocols(self, protocols: dict[Any, Any]) -> None:
        payment_app = protocols.get(BharatProtocol.PAYMENT)
        if payment_app is not None and payment_app is not self:
            self.payment_app = payment_app

    def require_payment_app(self) -> PaySetuApp:
        if self.payment_app is None:
            raise RuntimeError(f"{self.name} is not connected to PaySetu; register both apps in the same environment")
        return self.payment_app

    def charge(
        self,
        amount: int,
        payment: str,
        category: str,
        reference_id: str,
        merchant: str | None = None,
    ) -> str:
        return self.require_payment_app().charge(
            amount=amount,
            payment=payment,
            merchant=merchant or self.name,
            category=category,
            reference_app=self.name,
            reference_id=reference_id,
        )

    def refund(self, txn_id: str, amount: int) -> str | None:
        if amount <= 0:
            return None
        return self.require_payment_app().refund(txn_id=txn_id, amount=amount)

    def refund_cod(self, amount: int, reference_id: str) -> str | None:
        """Refund a cash-on-delivery order to the default bank account."""
        if amount <= 0:
            return None
        return self.require_payment_app().credit_default_account(
            amount=amount,
            counterparty_name=self.name,
            reference_app=self.name,
            reference_id=reference_id,
        )

    # Addresses -------------------------------------------------------------
    def save_address(
        self,
        addresses: dict[str, Address],
        prefix: str,
        label: str,
        line1: str,
        area: str,
        city: str,
        pincode: str,
        phone: str,
    ) -> str:
        if label not in ADDRESS_LABELS:
            raise ValueError(f"label must be one of {', '.join(ADDRESS_LABELS)}")
        if not (pincode.isdigit() and len(pincode) == 6):
            raise ValueError("pincode must be 6 digits")
        address = Address(self.next_id(prefix, 2), label, line1, area, city, pincode, phone)
        addresses[address.address_id] = address
        return address.address_id

    def address(self, addresses: dict[str, Address], address_id: str) -> Address:
        if address_id not in addresses:
            raise ValueError(f"Address {address_id} does not exist")
        return addresses[address_id]

    # State helpers ---------------------------------------------------------
    def base_state(self) -> dict[str, Any]:
        return {"id_counters": dict(self.id_counters)}

    def load_base_state(self, state: dict[str, Any]) -> None:
        self.id_counters = dict(state.get("id_counters", {}))
