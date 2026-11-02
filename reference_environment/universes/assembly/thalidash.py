"""ThaliDash state, with bills computed by ThaliDash's own fee rules, plus the PaySetu payments it implies."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from reference_environment.universes.apps import thalidash as rules
from reference_environment.universes.apps.common import COD, format_datetime, parse_datetime, percent_of

from .content import unique

WEEKDAYS = rules.WEEKDAYS


def _restaurant_record(raw: dict[str, Any]) -> dict[str, Any]:
    record = {key: value for key, value in raw.items() if key not in ("daily_hours", "menu")}
    record["open_hours"] = raw.get("open_hours") or {day: raw["daily_hours"] for day in WEEKDAYS}
    record["menu"] = [
        {"item_id": item_id, "name": name, "category": category, "price": price, "veg": veg, "available": True}
        for item_id, name, category, price, veg in raw["menu"]
    ]
    record.setdefault("closed_until", None)
    return record


def _bill(
    order: dict[str, Any],
    restaurant: dict[str, Any],
    coupons: dict[str, dict[str, Any]],
    subscription: dict[str, Any] | None,
) -> dict[str, Any]:
    menu = {item["item_id"]: item for item in restaurant["menu"]}
    lines = []
    for item_id, quantity in order["items"]:
        if item_id not in menu:
            raise ValueError(f"{order['order_id']}: {item_id} is not on {restaurant['name']}'s menu")
        item = menu[item_id]
        lines.append({"item_id": item_id, "name": item["name"], "quantity": quantity, "price": item["price"]})
    item_total = sum(line["price"] * line["quantity"] for line in lines)
    discount = 0
    if order.get("coupon_code"):
        coupon = coupons[order["coupon_code"]]
        if coupon.get("restaurant_ids") and restaurant["restaurant_id"] not in coupon["restaurant_ids"]:
            raise ValueError(f"{order['order_id']}: coupon {coupon['code']} not valid at {restaurant['name']}")
        if item_total < coupon["min_order"]:
            raise ValueError(f"{order['order_id']}: item total {item_total} below {coupon['code']} minimum")
        if coupon["discount_type"] == "percent":
            discount = min(percent_of(item_total, coupon["value"]), coupon["max_discount"])
        else:
            discount = min(coupon["value"], item_total)
    free = item_total >= rules.FREE_DELIVERY_FROM and restaurant["distance_km"] <= rules.FREE_DELIVERY_MAX_KM
    if subscription and order["placed_at"][:10] <= subscription["valid_until"]:
        free = free or restaurant["distance_km"] <= subscription["free_delivery_max_km"]
    bill = {
        "items": lines,
        "item_total": item_total,
        "delivery_fee": 0 if free else rules.DELIVERY_FEE,
        "platform_fee": rules.PLATFORM_FEE,
        "packaging_fee": restaurant["packaging_fee"],
        "gst": percent_of(item_total, rules.GST_PERCENT),
        "discount": discount,
    }
    charges = ("item_total", "delivery_fee", "platform_fee", "packaging_fee", "gst")
    bill["total"] = sum(bill[k] for k in charges) - discount
    return bill


def _open_at(restaurant: dict[str, Any], moment: str) -> bool:
    when = parse_datetime(moment)
    clock = when.strftime("%H:%M")
    return any(start <= clock < end for start, end in restaurant["open_hours"][WEEKDAYS[when.weekday()]])


def build_thalidash(content: dict[str, Any], addresses: dict[str, dict[str, Any]], phone: str):
    """Return (ThaliDash state, PaySetu payments) where payments carry local keys resolved later."""
    restaurants = {r["restaurant_id"]: _restaurant_record(r) for r in content["restaurants"]}
    coupons = {c["code"]: {"restaurant_ids": [], **c} for c in unique(content["coupons"], "code", "coupon").values()}
    state_addresses = {}
    for entry in content["addresses"]:
        address = addresses[entry["address_key"]]
        state_addresses[entry["address_id"]] = {
            "address_id": entry["address_id"],
            "label": address["label"],
            "line1": address["line1"],
            "area": address["area"],
            "city": address["city"],
            "pincode": address["pincode"],
            "phone": phone,
        }
    orders, payments = {}, []
    for order in sorted(unique(content["orders"], "order_id", "order").values(), key=lambda o: o["placed_at"]):
        restaurant = restaurants[order["restaurant_id"]]
        if not _open_at(restaurant, order["placed_at"]):
            raise ValueError(f"{order['order_id']}: {restaurant['name']} is closed at {order['placed_at']}")
        bill = _bill(order, restaurant, coupons, content.get("subscription"))
        status = order.get("status", "delivered")
        placed = parse_datetime(order["placed_at"])
        txn_key = None
        if order["payment"] != COD:
            txn_key = f"order:{order['order_id']}"
            payments.append(
                {
                    "key": txn_key,
                    "timestamp": order["placed_at"],
                    "direction": "debit",
                    "amount": bill["total"],
                    "counterparty_name": restaurant["name"],
                    "source_id": order["payment"],
                    "category": "food",
                    "reference_app": "ThaliDash",
                    "reference_id": order["order_id"],
                }
            )
            if status == "cancelled":
                payments.append(
                    {
                        "key": f"refund:{order['order_id']}",
                        "timestamp": order["cancelled_at"],
                        "direction": "credit",
                        "amount": bill["total"],
                        "counterparty_name": restaurant["name"],
                        "source_id": order["payment"],
                        "category": "refund",
                        "reference_app": "ThaliDash",
                        "reference_id": order["order_id"],
                        "refund_of_key": txn_key,
                    }
                )
        arrival = format_datetime(placed + timedelta(minutes=restaurant["delivery_time_min"]))
        orders[order["order_id"]] = {
            "order_id": order["order_id"],
            "restaurant_id": restaurant["restaurant_id"],
            **bill,
            "address_id": order["address_id"],
            "payment": order["payment"],
            "placed_at": order["placed_at"],
            "expected_delivery_at": arrival,
            "status": status,
            "coupon_code": order.get("coupon_code"),
            "txn_id": txn_key,
            "delivery_instructions": order.get("delivery_instructions", ""),
            "delivered_at": arrival if status == "delivered" else None,
            "rating": order.get("rating"),
            "refunded_amount": bill["total"] if status == "cancelled" and txn_key else 0,
        }
    reservations = {}
    for reservation in unique(content["reservations"], "reservation_id", "reservation").values():
        restaurant = restaurants[reservation["restaurant_id"]]
        if not restaurant["dine_in"] or not _open_at(restaurant, reservation["datetime"]):
            raise ValueError(f"{reservation['reservation_id']}: not a valid table booking")
        reservations[reservation["reservation_id"]] = {
            key: reservation.get(key, "")
            for key in ("reservation_id", "restaurant_id", "datetime", "guests", "status", "special_request")
        }
        if "bill" in reservation:
            payments.append(_meal_payment(reservation, restaurant, f"meal:{reservation['reservation_id']}"))
    for index, meal in enumerate(content.get("walk_in_meals", [])):
        payments.append(_meal_payment(meal, restaurants[meal["restaurant_id"]], f"walkin:{index}"))
    numbers = [int(order_id.rsplit("-", 1)[1]) for order_id in orders]
    reservation_numbers = [int(r.rsplit("-", 1)[1]) for r in reservations]
    state = {
        "id_counters": {"TD-ORD": max(numbers, default=0), "TD-RES": max(reservation_numbers, default=0)},
        "restaurants": restaurants,
        "coupons": coupons,
        "addresses": state_addresses,
        "cart": {},
        "cart_restaurant_id": None,
        "orders": orders,
        "reservations": reservations,
        "subscription": content.get("subscription"),
    }
    return state, payments


def _meal_payment(meal: dict[str, Any], restaurant: dict[str, Any], key: str) -> dict[str, Any]:
    paid_at = format_datetime(parse_datetime(meal["datetime"]) + timedelta(minutes=75))
    return {
        "key": key,
        "timestamp": paid_at,
        "direction": "debit",
        "amount": meal["bill"],
        "counterparty_name": restaurant["name"],
        "source_id": meal["paid_with"],
        "category": "food",
        "note": meal.get("note", "Dine-in bill"),
    }
