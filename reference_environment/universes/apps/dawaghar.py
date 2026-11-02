"""DawaGhar: online pharmacy modelled on 1mg.

Schema: app_schemas.md section 7. Prescription handling follows owner
decision #21: an order whose prescription-only items are not covered is held,
not charged, until a valid prescription is attached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from are.simulation.tool_utils import OperationType, app_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import type_check

from .common import (
    COD,
    Address,
    BharatApp,
    dump_records,
    load_records,
    page,
    parse_date,
    parse_datetime,
    to_dict,
)

DELIVERY_FEE = 49
FREE_DELIVERY_FROM = 300
COD_LIMIT = 2000
DELIVERY_DAYS = 2
HOLD_HOURS = 48
ORDER_FLOW = ("placed", "shipped", "delivered")


@dataclass
class Medicine:
    medicine_id: str
    name: str
    manufacturer: str
    composition: str
    form: str
    pack_size: str
    mrp: int
    price: int
    prescription_required: bool
    in_stock: bool = True


@dataclass
class Prescription:
    prescription_id: str
    patient_name: str
    doctor_name: str
    issued_on: str
    valid_until: str
    items: list[dict[str, Any]]
    file_path: str | None = None


@dataclass
class MedicineOrder:
    order_id: str
    items: list[dict[str, Any]]
    address_id: str
    item_total: int
    delivery_fee: int
    total: int
    payment: str
    placed_at: str
    status: str
    prescription_id: str | None = None
    txn_id: str | None = None
    expected_delivery: str | None = None
    uncovered_items: list[str] = field(default_factory=list)
    refunded_amount: int = 0


@dataclass
class RefillReminder:
    reminder_id: str
    medicine_id: str
    interval_days: int
    next_due: str


class DawaGharApp(BharatApp):
    """
    DawaGhar is an online pharmacy: search medicines by name or salt (composition), find cheaper substitutes,
    order with home delivery, and keep refill reminders.

    Notes:
        - Some medicines need a prescription. A prescription covers an item if it is not past valid_until and
          lists the item's composition.
        - If every prescription-only item is covered, the order is placed and charged at once. Otherwise the
          order is created "on_hold_prescription" and nothing is charged; attach_prescription with a valid
          prescription releases and charges it. Orders held for more than 48 hours are cancelled.
        - Substitutes have the same composition and form.
        - Delivery is 49 rupees below an item total of 300, otherwise free. Cash on delivery ("cod") is allowed
          up to 2000 rupees. Orders can be cancelled while placed or on hold.
        - Dates use YYYY-MM-DD and times are local (IST). Amounts are whole rupees.
    """

    def __init__(self, name: str | None = "DawaGhar") -> None:
        super().__init__(name)
        self.medicines: dict[str, Medicine] = {}
        self.prescriptions: dict[str, Prescription] = {}
        self.addresses: dict[str, Address] = {}
        self.cart: dict[str, int] = {}
        self.orders: dict[str, MedicineOrder] = {}
        self.refill_reminders: dict[str, RefillReminder] = {}

    # State -----------------------------------------------------------------
    def get_state(self) -> dict[str, Any]:
        return {
            **self.base_state(),
            "medicines": dump_records(self.medicines),
            "prescriptions": dump_records(self.prescriptions),
            "addresses": dump_records(self.addresses),
            "cart": dict(self.cart),
            "orders": dump_records(self.orders),
            "refill_reminders": dump_records(self.refill_reminders),
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self.load_base_state(state_dict)
        self.medicines = load_records(Medicine, state_dict.get("medicines", {}))
        self.prescriptions = load_records(Prescription, state_dict.get("prescriptions", {}))
        self.addresses = load_records(Address, state_dict.get("addresses", {}))
        self.cart = dict(state_dict.get("cart", {}))
        self.orders = load_records(MedicineOrder, state_dict.get("orders", {}))
        self.refill_reminders = load_records(RefillReminder, state_dict.get("refill_reminders", {}))

    # Helpers -----------------------------------------------------------------
    def _medicine(self, medicine_id: str) -> Medicine:
        if medicine_id not in self.medicines:
            raise ValueError(f"Medicine {medicine_id} does not exist")
        return self.medicines[medicine_id]

    def _prescription(self, prescription_id: str) -> Prescription:
        if prescription_id not in self.prescriptions:
            raise ValueError(f"Prescription {prescription_id} does not exist")
        return self.prescriptions[prescription_id]

    def _order(self, order_id: str) -> MedicineOrder:
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} does not exist")
        return self.orders[order_id]

    def _uncovered(self, items: list[dict[str, Any]], prescription_id: str | None) -> list[str]:
        """Names of prescription-only items the given prescription does not cover."""
        covered: set[str] = set()
        if prescription_id is not None:
            prescription = self._prescription(prescription_id)
            if self.today() <= parse_date(prescription.valid_until):
                covered = {entry["composition"].casefold() for entry in prescription.items}
        return [
            item["name"]
            for item in items
            if item["prescription_required"]
            and self._medicine(item["medicine_id"]).composition.casefold() not in covered
        ]

    def _release(self, order: MedicineOrder) -> None:
        """Charge a covered order and move it to placed."""
        if order.payment != COD:
            order.txn_id = self.charge(order.total, order.payment, "health", order.order_id, merchant="DawaGhar")
        order.status = "placed"
        order.uncovered_items = []
        order.expected_delivery = (self.today() + timedelta(days=DELIVERY_DAYS)).isoformat()

    # Read tools --------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_medicines(self, query: str) -> list[dict[str, Any]]:
        """
        Search medicines by brand name, manufacturer or composition (salt).
        :param query: e.g. "vitamin D3", "Cholecalciferol", "paracetamol 650"
        :returns: matching medicines with price, pack size and whether a prescription is needed
        """
        words = query.casefold().split()
        found = [
            medicine
            for medicine in self.medicines.values()
            if all(
                word in f"{medicine.name} {medicine.manufacturer} {medicine.composition}".casefold() for word in words
            )
        ]
        return [to_dict(m) for m in sorted(found, key=lambda m: (m.price, m.medicine_id))]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_medicine(self, medicine_id: str) -> dict[str, Any]:
        """
        Get one medicine.
        :param medicine_id: the medicine ID
        :returns: the medicine
        """
        return to_dict(self._medicine(medicine_id))

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def find_substitutes(self, medicine_id: str) -> list[dict[str, Any]]:
        """
        Find substitutes with the same composition and form, cheapest first.
        :param medicine_id: the medicine ID
        :returns: substitute medicines
        """
        original = self._medicine(medicine_id)
        found = [
            m
            for m in self.medicines.values()
            if m.medicine_id != medicine_id
            and m.composition.casefold() == original.composition.casefold()
            and m.form == original.form
        ]
        return [to_dict(m) for m in sorted(found, key=lambda m: (m.price, m.medicine_id))]

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_prescriptions(self) -> list[dict[str, Any]]:
        """
        List uploaded prescriptions, newest first.
        :returns: prescriptions with their items and validity
        """
        ordered = sorted(self.prescriptions.values(), key=lambda p: p.issued_on, reverse=True)
        return [to_dict(p) for p in ordered]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_prescription(self, prescription_id: str) -> dict[str, Any]:
        """
        Get one prescription.
        :param prescription_id: the prescription ID
        :returns: the prescription
        """
        return to_dict(self._prescription(prescription_id))

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_addresses(self) -> list[dict[str, Any]]:
        """
        List saved delivery addresses.
        :returns: addresses
        """
        return [to_dict(address) for address in self.addresses.values()]

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def view_cart(self) -> dict[str, Any]:
        """
        Show the cart with prices, delivery fee and total.
        :returns: cart lines and bill
        """
        lines = [
            {
                "medicine_id": medicine_id,
                "name": self._medicine(medicine_id).name,
                "quantity": quantity,
                "price": self._medicine(medicine_id).price,
                "prescription_required": self._medicine(medicine_id).prescription_required,
                "in_stock": self._medicine(medicine_id).in_stock,
            }
            for medicine_id, quantity in self.cart.items()
        ]
        item_total = sum(line["price"] * line["quantity"] for line in lines)
        fee = DELIVERY_FEE if lines and item_total < FREE_DELIVERY_FROM else 0
        return {"items": lines, "item_total": item_total, "delivery_fee": fee, "total": item_total + fee}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_orders(self, offset: int = 0, limit: int = 10) -> dict[str, Any]:
        """
        List medicine orders, newest first.
        :param offset: index of the first order to return
        :param limit: maximum number of orders to return
        :returns: a page of orders with the total count
        """
        ordered = sorted(self.orders.values(), key=lambda o: (o.placed_at, o.order_id), reverse=True)
        return page([to_dict(order) for order in ordered], offset, limit)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_order(self, order_id: str) -> dict[str, Any]:
        """
        Get one order, including which items are waiting for a prescription.
        :param order_id: the order ID
        :returns: the order
        """
        return to_dict(self._order(order_id))

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_refill_reminders(self) -> list[dict[str, Any]]:
        """
        List refill reminders with their next due date.
        :returns: reminders
        """
        return [
            {
                **to_dict(r),
                "medicine_name": self.medicines[r.medicine_id].name if r.medicine_id in self.medicines else None,
            }
            for r in sorted(self.refill_reminders.values(), key=lambda r: r.next_due)
        ]

    # Write tools -----------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_to_cart(self, medicine_id: str, quantity: int = 1) -> dict[str, int]:
        """
        Add packs of a medicine to the cart.
        :param medicine_id: the medicine ID
        :param quantity: number of packs
        :returns: the cart as medicine ID to quantity
        """
        if quantity <= 0:
            raise ValueError("quantity must be at least 1")
        medicine = self._medicine(medicine_id)
        if not medicine.in_stock:
            raise ValueError(f"{medicine.name} is out of stock; see find_substitutes")
        self.cart[medicine_id] = self.cart.get(medicine_id, 0) + quantity
        return dict(self.cart)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_from_cart(self, medicine_id: str, quantity: int = 1) -> dict[str, int]:
        """
        Remove packs of a medicine from the cart.
        :param medicine_id: the medicine ID
        :param quantity: number of packs to remove
        :returns: the cart as medicine ID to quantity
        """
        if medicine_id not in self.cart:
            raise ValueError(f"Medicine {medicine_id} is not in the cart")
        if quantity <= 0 or quantity > self.cart[medicine_id]:
            raise ValueError(f"quantity must be between 1 and {self.cart[medicine_id]}")
        self.cart[medicine_id] -= quantity
        if self.cart[medicine_id] == 0:
            del self.cart[medicine_id]
        return dict(self.cart)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def place_order(self, address_id: str, payment: str, prescription_id: str | None = None) -> dict[str, Any]:
        """
        Order everything in the cart. If a prescription-only item is not covered by a valid prescription,
        the order is held (status "on_hold_prescription") and not charged until attach_prescription succeeds.
        :param address_id: delivery address ID from list_addresses
        :param payment: PaySetu source_id to pay with, or "cod" for cash on delivery
        :param prescription_id: optional prescription covering the prescription-only items
        :returns: the new order, with uncovered_items listing anything waiting for a prescription
        """
        self.address(self.addresses, address_id)
        if not self.cart:
            raise ValueError("Cart is empty")
        items = []
        for medicine_id, quantity in self.cart.items():
            medicine = self._medicine(medicine_id)
            if not medicine.in_stock:
                raise ValueError(f"{medicine.name} is out of stock; remove it or choose a substitute")
            items.append(
                {
                    "medicine_id": medicine_id,
                    "name": medicine.name,
                    "quantity": quantity,
                    "price": medicine.price,
                    "prescription_required": medicine.prescription_required,
                }
            )
        item_total = sum(item["price"] * item["quantity"] for item in items)
        delivery_fee = DELIVERY_FEE if item_total < FREE_DELIVERY_FROM else 0
        total = item_total + delivery_fee
        if payment == COD and total > COD_LIMIT:
            raise ValueError(f"Cash on delivery is allowed only up to {COD_LIMIT} rupees")
        uncovered = self._uncovered(items, prescription_id)
        order = MedicineOrder(
            order_id=self.next_id("DG-ORD"),
            items=items,
            address_id=address_id,
            item_total=item_total,
            delivery_fee=delivery_fee,
            total=total,
            payment=payment,
            placed_at=self.now_str(),
            status="on_hold_prescription",
            prescription_id=prescription_id,
            uncovered_items=uncovered,
        )
        if not uncovered:
            self._release(order)
        self.orders[order.order_id] = order
        self.cart = {}
        return to_dict(order)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def attach_prescription(self, order_id: str, prescription_id: str) -> dict[str, Any]:
        """
        Attach a prescription to an order that is on hold. If it covers every prescription-only item,
        the order is placed and charged; otherwise it stays on hold and an error names the uncovered items.
        :param order_id: the order ID
        :param prescription_id: the prescription ID
        :returns: the updated order
        """
        order = self._order(order_id)
        if order.status != "on_hold_prescription":
            raise ValueError(f"Order {order_id} is not waiting for a prescription (status: {order.status})")
        uncovered = self._uncovered(order.items, prescription_id)
        if uncovered:
            raise ValueError(f"Prescription {prescription_id} is expired or does not cover: {', '.join(uncovered)}")
        order.prescription_id = prescription_id
        self._release(order)
        return to_dict(order)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """
        Cancel an order that is placed or on hold. A charged order is refunded in full.
        :param order_id: the order ID
        :returns: the refund amount and the updated order
        """
        order = self._order(order_id)
        if order.status not in ("placed", "on_hold_prescription"):
            raise ValueError(f"Order {order_id} cannot be cancelled, current status: {order.status}")
        refund = order.total if order.txn_id and not order.refunded_amount else 0
        if refund:
            self.refund(order.txn_id, refund)
            order.refunded_amount = refund
        order.status = "cancelled"
        return {"refund": refund, "order": to_dict(order)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def set_refill_reminder(self, medicine_id: str, interval_days: int) -> str:
        """
        Remind the user to reorder a medicine every interval_days, starting interval_days from today.
        :param medicine_id: the medicine ID
        :param interval_days: days between refills
        :returns: the reminder ID
        """
        self._medicine(medicine_id)
        if interval_days <= 0:
            raise ValueError("interval_days must be positive")
        if any(r.medicine_id == medicine_id for r in self.refill_reminders.values()):
            raise ValueError("A refill reminder for this medicine already exists; delete it first")
        reminder = RefillReminder(
            reminder_id=self.next_id("DG-REM", 3),
            medicine_id=medicine_id,
            interval_days=interval_days,
            next_due=(self.today() + timedelta(days=interval_days)).isoformat(),
        )
        self.refill_reminders[reminder.reminder_id] = reminder
        return reminder.reminder_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def delete_refill_reminder(self, reminder_id: str) -> str:
        """
        Delete a refill reminder.
        :param reminder_id: the reminder ID
        :returns: the deleted reminder ID
        """
        if reminder_id not in self.refill_reminders:
            raise ValueError(f"Reminder {reminder_id} does not exist")
        del self.refill_reminders[reminder_id]
        return reminder_id

    # Environment events -------------------------------------------------------
    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_medicine_order_status(self, order_id: str, status: str) -> None:
        """
        Move an order forward: placed, shipped, delivered.
        :param order_id: the order ID
        :param status: the new status
        """
        order = self._order(order_id)
        if status not in ORDER_FLOW or order.status not in ORDER_FLOW:
            raise ValueError(f"Cannot move order {order_id} from {order.status} to {status}")
        if ORDER_FLOW.index(status) <= ORDER_FLOW.index(order.status):
            raise ValueError(f"Order {order_id} is already {order.status}")
        order.status = status

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def set_medicine_stock(self, medicine_id: str, in_stock: bool) -> None:
        """
        Mark a medicine in or out of stock.
        :param medicine_id: the medicine ID
        :param in_stock: whether it can be ordered
        """
        self._medicine(medicine_id).in_stock = in_stock

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def hold_for_prescription(self, order_id: str, item_names: list[str]) -> None:
        """
        A pharmacist puts a placed order on hold because its prescription does not cover some items.
        Any charge is refunded; attach_prescription charges again once a valid prescription is attached.
        :param order_id: the order ID
        :param item_names: names of the items the pharmacist could not verify
        """
        order = self._order(order_id)
        if order.status != "placed":
            raise ValueError(f"Order {order_id} is {order.status}, not placed")
        if order.txn_id:
            self.refund(order.txn_id, order.total)
            order.txn_id = None
        order.status = "on_hold_prescription"
        order.uncovered_items = list(item_names)

    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def expire_held_orders(self) -> list[str]:
        """
        Cancel orders that have waited for a prescription for more than 48 hours.
        :returns: IDs of cancelled orders
        """
        expired = []
        for order in self.orders.values():
            if (
                order.status == "on_hold_prescription"
                and self.hours_until(parse_datetime(order.placed_at)) <= -HOLD_HOURS
            ):
                order.status = "cancelled"
                expired.append(order.order_id)
        return expired
