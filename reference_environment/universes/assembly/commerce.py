"""KartBazaar and StyleGali state, with bills from each store's own rules, plus the PaySetu payments."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from reference_environment.universes.apps.commerce import CommerceApp
from reference_environment.universes.apps.common import COD, parse_datetime, round_rupees

from .content import unique

PRODUCT_FIELDS = ("brand", "category", "seller", "description", "delivery_days", "cod_available", "return_policy")


def _product(raw: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    record = {
        "product_id": raw["id"],
        "name": raw["name"],
        "rating": raw["rating"],
        "review_count": raw["reviews"],
        "return_window_days": raw.get("return_window_days", defaults["return_window_days"]),
        "variants": {
            item_id: {"item_id": item_id, "price": price, "available": available, "options": options}
            for item_id, price, available, options in raw["variants"]
        },
    }
    for field in PRODUCT_FIELDS:
        record[field] = raw.get(field, defaults.get(field))
    return record


def build_commerce(
    content: dict[str, Any],
    store: type[CommerceApp],
    addresses: dict[str, dict[str, Any]],
    phones: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (store state, PaySetu payments with local keys)."""
    defaults = content["defaults"]
    products = {p["id"]: _product(p, defaults) for p in unique(content["products"], "id", "product").values()}
    items = {
        item_id: (product, variant) for product in products.values() for item_id, variant in product["variants"].items()
    }
    codes = {
        c["code"]: {
            "code": c["code"],
            "percent": c["percent"],
            "item_ids": c["item_ids"],
            "description": c.get("description", ""),
        }
        for c in unique(content.get("discount_codes", []), "code", "discount code").values()
    }
    for code in codes.values():
        missing = set(code["item_ids"]) - set(items)
        if missing:
            raise ValueError(f"Discount code {code['code']} names unknown items {sorted(missing)}")
    state_addresses = {}
    for entry in content["addresses"]:
        address = addresses[entry["address_key"]]
        state_addresses[entry["address_id"]] = {
            "address_id": entry["address_id"],
            **{key: address[key] for key in ("label", "line1", "area", "city", "pincode")},
            "phone": phones[address["phone_person"]],
        }
    orders, payments = {}, []
    for order in sorted(unique(content.get("orders", []), "order_id", "order").values(), key=lambda o: o["placed_at"]):
        code = codes.get(order.get("discount_code")) if order.get("discount_code") else None
        lines, item_total, discount = [], 0, Decimal(0)
        for item_id, quantity in order["items"]:
            product, variant = items[item_id]
            if code is not None and item_id not in code["item_ids"]:
                raise ValueError(f"{order['order_id']}: {code['code']} does not cover {item_id}")
            line_total = variant["price"] * quantity
            item_total += line_total
            if code is not None:
                discount += Decimal(line_total) * Decimal(str(code["percent"])) / Decimal(100)
            lines.append(
                {
                    "item_id": item_id,
                    "product_id": product["product_id"],
                    "name": product["name"],
                    "options": dict(variant["options"]),
                    "quantity": quantity,
                    "price": variant["price"],
                    "return_status": "none",
                }
            )
        discount_rupees = round_rupees(discount)
        after = item_total - discount_rupees
        delivery_fee = 0 if after >= store.FREE_DELIVERY_FROM else store.DELIVERY_FEE
        total = after + delivery_fee
        if order["payment"] == COD and (
            total > store.COD_LIMIT or not all(items[i][0]["cod_available"] for i, _ in order["items"])
        ):
            raise ValueError(f"{order['order_id']}: cash on delivery is not allowed")
        history = [{"status": "placed", "at": order["placed_at"]}]
        status = "placed"
        for step in ("shipped", "delivered"):
            if order.get(f"{step}_at"):
                history.append({"status": step, "at": order[f"{step}_at"]})
                status = step
        key = None
        if order["payment"] != COD:
            key = f"shop:{order['order_id']}"
            payments.append(
                {
                    "key": key,
                    "timestamp": order["placed_at"],
                    "direction": "debit",
                    "amount": total,
                    "counterparty_name": store.__name__.removesuffix("App"),
                    "source_id": order["payment"],
                    "category": "shopping",
                    "reference_app": store.__name__.removesuffix("App"),
                    "reference_id": order["order_id"],
                }
            )
        days = max(items[item_id][0]["delivery_days"] for item_id, _ in order["items"])
        orders[order["order_id"]] = {
            "order_id": order["order_id"],
            "items": lines,
            "item_total": item_total,
            "discount": discount_rupees,
            "delivery_fee": delivery_fee,
            "total": total,
            "address_id": order["address_id"],
            "payment": order["payment"],
            "placed_at": order["placed_at"],
            "expected_delivery": (parse_datetime(order["placed_at"]).date() + timedelta(days=days)).isoformat(),
            "status": status,
            "discount_code": code["code"] if code else None,
            "txn_id": key,
            "delivered_at": order.get("delivered_at"),
            "refunded_amount": 0,
            "history": history,
        }
    wishlist = list(content.get("wishlist", []))
    unknown = [item_id for item_id in wishlist if item_id not in items]
    if unknown:
        raise ValueError(f"Wishlist has unknown items {unknown}")
    state = {
        "id_counters": {store.ORDER_PREFIX: len(orders), f"{store.ORDER_PREFIX}-ADDR": len(state_addresses)},
        "products": products,
        "discount_codes": codes,
        "addresses": state_addresses,
        "cart": {},
        "wishlist": wishlist,
        "orders": orders,
    }
    return state, payments
