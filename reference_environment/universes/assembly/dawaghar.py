"""DawaGhar state, with bills from DawaGhar's own rules and prescription checks, plus the PaySetu payments."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from reference_environment.universes.apps import dawaghar as rules
from reference_environment.universes.apps.common import COD, parse_date, parse_datetime

from .content import unique


def build_dawaghar(
    content: dict[str, Any], addresses: dict[str, dict[str, Any]], phone: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (DawaGhar state, PaySetu payments with local keys)."""
    medicines = {m["medicine_id"]: {"in_stock": True, **m} for m in content["medicines"]}
    prescriptions = {
        p["prescription_id"]: {"file_path": None, **p}
        for p in unique(content.get("prescriptions", []), "prescription_id", "prescription").values()
    }
    state_addresses = {}
    for entry in content["addresses"]:
        address = addresses[entry["address_key"]]
        state_addresses[entry["address_id"]] = {
            "address_id": entry["address_id"],
            **{key: address[key] for key in ("label", "line1", "area", "city", "pincode")},
            "phone": phone,
        }
    orders, payments = {}, []
    for order in sorted(unique(content["orders"], "order_id", "order").values(), key=lambda o: o["placed_at"]):
        items = []
        for medicine_id, quantity in order["items"]:
            medicine = medicines[medicine_id]
            items.append(
                {
                    "medicine_id": medicine_id,
                    "name": medicine["name"],
                    "quantity": quantity,
                    "price": medicine["price"],
                    "prescription_required": medicine["prescription_required"],
                }
            )
        placed = parse_datetime(order["placed_at"])
        prescription = prescriptions.get(order.get("prescription_id"))
        covered = set()
        if prescription and placed.date() <= parse_date(prescription["valid_until"]):
            covered = {entry["composition"].casefold() for entry in prescription["items"]}
        uncovered = [
            item["name"]
            for item in items
            if item["prescription_required"] and medicines[item["medicine_id"]]["composition"].casefold() not in covered
        ]
        if uncovered and order["status"] != "on_hold_prescription":
            raise ValueError(f"{order['order_id']}: {uncovered} not covered by a valid prescription")
        item_total = sum(item["price"] * item["quantity"] for item in items)
        delivery_fee = rules.DELIVERY_FEE if item_total < rules.FREE_DELIVERY_FROM else 0
        total = item_total + delivery_fee
        key = None
        if order["payment"] != COD and not uncovered:
            key = f"medicine:{order['order_id']}"
            payments.append(
                {
                    "key": key,
                    "timestamp": order["placed_at"],
                    "direction": "debit",
                    "amount": total,
                    "counterparty_name": "DawaGhar",
                    "source_id": order["payment"],
                    "category": "health",
                    "reference_app": "DawaGhar",
                    "reference_id": order["order_id"],
                }
            )
        orders[order["order_id"]] = {
            "order_id": order["order_id"],
            "items": items,
            "address_id": order["address_id"],
            "item_total": item_total,
            "delivery_fee": delivery_fee,
            "total": total,
            "payment": order["payment"],
            "placed_at": order["placed_at"],
            "status": order["status"],
            "prescription_id": order.get("prescription_id"),
            "txn_id": key,
            "expected_delivery": (placed.date() + timedelta(days=rules.DELIVERY_DAYS)).isoformat(),
            "uncovered_items": uncovered,
            "refunded_amount": 0,
        }
    reminders = unique(content.get("refill_reminders", []), "reminder_id", "refill reminder")
    state = {
        "id_counters": {"DG-ORD": len(orders), "DG-REM": len(reminders)},
        "medicines": medicines,
        "prescriptions": prescriptions,
        "addresses": state_addresses,
        "cart": {},
        "orders": orders,
        "refill_reminders": reminders,
    }
    return state, payments
