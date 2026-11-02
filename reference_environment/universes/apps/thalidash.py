"""ThaliDash: food delivery and table reservations, modelled on Swiggy / Zomato.

Schema: app_schemas.md section 5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from are.simulation.tool_utils import OperationType, app_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import type_check

from .common import (
    COD,
    Address,
    BharatApp,
    dump_records,
    format_datetime,
    load_records,
    matches,
    page,
    parse_date,
    parse_datetime,
    percent_of,
    to_dict,
)

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
DELIVERY_FEE = 35
FREE_DELIVERY_FROM = 499
FREE_DELIVERY_MAX_KM = 5.0
PLATFORM_FEE = 10
GST_PERCENT = 5
COD_BELOW = 1500
MAX_TABLE_GUESTS = 12
ORDER_FLOW = ("placed", "preparing", "out_for_delivery", "delivered")


@dataclass
class Restaurant:
    restaurant_id: str
    name: str
    area: str
    cuisines: list[str]
    veg_only: bool
    rating: float
    cost_for_two: int
    distance_km: float
    delivery_time_min: int
    open_hours: dict[str, list[list[str]]]
    packaging_fee: int
    dine_in: bool
    menu: list[dict[str, Any]]
    closed_until: str | None = None


@dataclass
class Coupon:
    code: str
    description: str
    discount_type: str
    value: int
    max_discount: int
    min_order: int
    valid_until: str
    uses_left: int
    restaurant_ids: list[str] = field(default_factory=list)


@dataclass
class Subscription:
    plan: str
    valid_until: str
    free_delivery_max_km: float


@dataclass
class FoodOrder:
    order_id: str
    restaurant_id: str
    items: list[dict[str, Any]]
    item_total: int
    delivery_fee: int
    platform_fee: int
    packaging_fee: int
    gst: int
    discount: int
    total: int
    address_id: str
    payment: str
    placed_at: str
    expected_delivery_at: str
    status: str = "placed"
    coupon_code: str | None = None
    txn_id: str | None = None
    delivery_instructions: str = ""
    delivered_at: str | None = None
    rating: int | None = None
    refunded_amount: int = 0


@dataclass
class Reservation:
    reservation_id: str
    restaurant_id: str
    datetime: str
    guests: int
    status: str = "confirmed"
    special_request: str = ""


class ThaliDashApp(BharatApp):
    """
    ThaliDash orders food from nearby restaurants and books tables for dining out.

    Notes:
        - The cart holds items from one restaurant only; clear it before adding items from another restaurant.
        - Bill = item total + delivery fee (35 rupees; free when the item total is 499 or more and the
          restaurant is within 5 km) + platform fee (10) + the restaurant's packaging fee + GST (5% of the
          item total) - coupon discount.
        - With an active subscription (see get_subscription), delivery is free at any order value from
          restaurants within the plan's distance; farther restaurants still charge the delivery fee.
        - One coupon per order. A coupon needs the minimum item total, an eligible restaurant, a valid date
          and uses left; percentage coupons are capped at their max_discount.
        - Orders can be placed only while the restaurant is open, and cancelled (full refund) only before the
          restaurant starts preparing. Cash on delivery ("cod") is not allowed for totals of 1500 rupees or more.
        - Tables can be booked at dine-in restaurants, during opening hours, for up to 12 guests, at least 1 hour ahead.
        - Times are local (IST) in the format YYYY-MM-DD HH:MM:SS. Amounts are whole rupees.
    """

    def __init__(self, name: str | None = "ThaliDash") -> None:
        super().__init__(name)
        self.restaurants: dict[str, Restaurant] = {}
        self.coupons: dict[str, Coupon] = {}
        self.addresses: dict[str, Address] = {}
        self.cart: dict[str, int] = {}
        self.cart_restaurant_id: str | None = None
        self.orders: dict[str, FoodOrder] = {}
        self.reservations: dict[str, Reservation] = {}
        self.subscription: Subscription | None = None

    # State -----------------------------------------------------------------
    def get_state(self) -> dict[str, Any]:
        return {
            **self.base_state(),
            "restaurants": dump_records(self.restaurants),
            "coupons": dump_records(self.coupons),
            "addresses": dump_records(self.addresses),
            "cart": dict(self.cart),
            "cart_restaurant_id": self.cart_restaurant_id,
            "orders": dump_records(self.orders),
            "reservations": dump_records(self.reservations),
            "subscription": to_dict(self.subscription) if self.subscription else None,
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self.load_base_state(state_dict)
        self.restaurants = load_records(Restaurant, state_dict.get("restaurants", {}))
        self.coupons = load_records(Coupon, state_dict.get("coupons", {}))
        self.addresses = load_records(Address, state_dict.get("addresses", {}))
        self.cart = dict(state_dict.get("cart", {}))
        self.cart_restaurant_id = state_dict.get("cart_restaurant_id")
        self.orders = load_records(FoodOrder, state_dict.get("orders", {}))
        self.reservations = load_records(Reservation, state_dict.get("reservations", {}))
        subscription = state_dict.get("subscription")
        self.subscription = Subscription(**subscription) if subscription else None

    # Helpers -----------------------------------------------------------------
    def _restaurant(self, restaurant_id: str) -> Restaurant:
        if restaurant_id not in self.restaurants:
            raise ValueError(f"Restaurant {restaurant_id} does not exist")
        return self.restaurants[restaurant_id]

    def _menu_item(self, item_id: str) -> tuple[Restaurant, dict[str, Any]]:
        for restaurant in self.restaurants.values():
            for item in restaurant.menu:
                if item["item_id"] == item_id:
                    return restaurant, item
        raise ValueError(f"Menu item {item_id} does not exist")

    def _order(self, order_id: str) -> FoodOrder:
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} does not exist")
        return self.orders[order_id]

    @staticmethod
    def _within_hours(restaurant: Restaurant, moment: datetime) -> bool:
        clock = moment.strftime("%H:%M")
        windows = restaurant.open_hours.get(WEEKDAYS[moment.weekday()], [])
        return any(start <= clock < end for start, end in windows)

    def _is_open(self, restaurant: Restaurant, moment: datetime) -> bool:
        if restaurant.closed_until and moment < parse_datetime(restaurant.closed_until):
            return False
        return self._within_hours(restaurant, moment)

    def _coupon_discount(self, coupon_code: str, restaurant: Restaurant, item_total: int) -> tuple[Coupon, int]:
        coupon = self.coupons.get(coupon_code.strip())
        if coupon is None:
            raise ValueError(f"Coupon {coupon_code} does not exist")
        if coupon.restaurant_ids and restaurant.restaurant_id not in coupon.restaurant_ids:
            raise ValueError(f"Coupon {coupon.code} is not valid at {restaurant.name}")
        if self.today() > parse_date(coupon.valid_until):
            raise ValueError(f"Coupon {coupon.code} expired on {coupon.valid_until}")
        if coupon.uses_left <= 0:
            raise ValueError(f"Coupon {coupon.code} has no uses left")
        if item_total < coupon.min_order:
            raise ValueError(f"Coupon {coupon.code} needs an item total of at least {coupon.min_order} rupees")
        if coupon.discount_type == "percent":
            return coupon, min(percent_of(item_total, coupon.value), coupon.max_discount)
        return coupon, min(coupon.value, item_total)

    def _bill(self, coupon_code: str | None) -> dict[str, Any]:
        if not self.cart or self.cart_restaurant_id is None:
            raise ValueError("Cart is empty")
        restaurant = self._restaurant(self.cart_restaurant_id)
        lines = []
        for item_id, quantity in self.cart.items():
            _, item = self._menu_item(item_id)
            if not item["available"]:
                raise ValueError(f"{item['name']} is currently unavailable; remove it from the cart")
            lines.append({"item_id": item_id, "name": item["name"], "quantity": quantity, "price": item["price"]})
        item_total = sum(line["price"] * line["quantity"] for line in lines)
        coupon, discount = (None, 0)
        if coupon_code:
            coupon, discount = self._coupon_discount(coupon_code, restaurant, item_total)
        free_delivery = (
            item_total >= FREE_DELIVERY_FROM and restaurant.distance_km <= FREE_DELIVERY_MAX_KM
        ) or self._subscription_covers(restaurant)
        bill = {
            "restaurant_id": restaurant.restaurant_id,
            "restaurant_name": restaurant.name,
            "items": lines,
            "item_total": item_total,
            "delivery_fee": 0 if free_delivery else DELIVERY_FEE,
            "platform_fee": PLATFORM_FEE,
            "packaging_fee": restaurant.packaging_fee,
            "gst": percent_of(item_total, GST_PERCENT),
            "discount": discount,
            "coupon_code": coupon.code if coupon else None,
        }
        bill["total"] = (
            bill["item_total"]
            + bill["delivery_fee"]
            + bill["platform_fee"]
            + bill["packaging_fee"]
            + bill["gst"]
            - discount
        )
        return bill

    def _subscription_covers(self, restaurant: Restaurant) -> bool:
        subscription = self.subscription
        return (
            subscription is not None
            and self.today() <= parse_date(subscription.valid_until)
            and restaurant.distance_km <= subscription.free_delivery_max_km
        )

    def _menu_summary(self, restaurant: Restaurant) -> dict[str, Any]:
        return {
            "restaurant_id": restaurant.restaurant_id,
            "name": restaurant.name,
            "area": restaurant.area,
            "cuisines": list(restaurant.cuisines),
            "veg_only": restaurant.veg_only,
            "rating": restaurant.rating,
            "cost_for_two": restaurant.cost_for_two,
            "distance_km": restaurant.distance_km,
            "delivery_time_min": restaurant.delivery_time_min,
            "open_now": self._is_open(restaurant, self.now()),
            "dine_in": restaurant.dine_in,
        }

    # Read tools --------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_restaurants(
        self,
        query: str | None = None,
        cuisine: str | None = None,
        veg_only: bool = False,
        open_now: bool = False,
        sort_by: str = "relevance",
    ) -> list[dict[str, Any]]:
        """
        Search restaurants by name, dish or cuisine.
        :param query: words matched against the restaurant name, cuisines and menu item names
        :param cuisine: only restaurants serving this cuisine, e.g. "Assamese"
        :param veg_only: only pure-vegetarian restaurants
        :param open_now: only restaurants open right now
        :param sort_by: "relevance", "rating", "delivery_time", "distance" or "cost_low"
        :returns: restaurant summaries
        """
        found = []
        for restaurant in self.restaurants.values():
            dishes = " ".join(item["name"] for item in restaurant.menu)
            if not matches(query, restaurant.name, " ".join(restaurant.cuisines), dishes):
                continue
            if cuisine and not any(matches(cuisine, c) for c in restaurant.cuisines):
                continue
            if veg_only and not restaurant.veg_only:
                continue
            summary = self._menu_summary(restaurant)
            if open_now and not summary["open_now"]:
                continue
            found.append(summary)
        keys = {
            "relevance": lambda r: r["restaurant_id"],
            "rating": lambda r: (-r["rating"], r["restaurant_id"]),
            "delivery_time": lambda r: (r["delivery_time_min"], r["restaurant_id"]),
            "distance": lambda r: (r["distance_km"], r["restaurant_id"]),
            "cost_low": lambda r: (r["cost_for_two"], r["restaurant_id"]),
        }
        if sort_by not in keys:
            raise ValueError("sort_by must be relevance, rating, delivery_time, distance or cost_low")
        return sorted(found, key=keys[sort_by])

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_restaurant(self, restaurant_id: str) -> dict[str, Any]:
        """
        Get a restaurant with its full menu, opening hours and fees.
        :param restaurant_id: the restaurant ID
        :returns: the restaurant
        """
        restaurant = self._restaurant(restaurant_id)
        return {**to_dict(restaurant), "open_now": self._is_open(restaurant, self.now())}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_coupons(self, restaurant_id: str | None = None) -> list[dict[str, Any]]:
        """
        List coupons that are still valid, optionally only those usable at one restaurant.
        :param restaurant_id: optional restaurant ID
        :returns: coupons
        """
        return [
            to_dict(coupon)
            for coupon in self.coupons.values()
            if self.today() <= parse_date(coupon.valid_until)
            and coupon.uses_left > 0
            and (restaurant_id is None or not coupon.restaurant_ids or restaurant_id in coupon.restaurant_ids)
        ]

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_subscription(self) -> dict[str, Any] | None:
        """
        Show the user's ThaliDash subscription, if any: plan, validity and the distance within which
        delivery is free.
        :returns: the subscription with an "active" flag, or None when there is none
        """
        if self.subscription is None:
            return None
        return {**to_dict(self.subscription), "active": self.today() <= parse_date(self.subscription.valid_until)}

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_addresses(self) -> list[dict[str, Any]]:
        """
        List saved delivery addresses.
        :returns: addresses
        """
        return [to_dict(address) for address in self.addresses.values()]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def view_cart(self, coupon_code: str | None = None) -> dict[str, Any]:
        """
        Show the cart with the full bill, optionally previewing a coupon.
        :param coupon_code: optional coupon to preview
        :returns: cart lines and bill breakdown
        """
        if not self.cart:
            return {"items": [], "total": 0}
        return self._bill(coupon_code)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_orders(self, offset: int = 0, limit: int = 10) -> dict[str, Any]:
        """
        List past and current food orders, newest first.
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
        Get one food order with its bill and status.
        :param order_id: the order ID
        :returns: the order
        """
        return to_dict(self._order(order_id))

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_reservations(self, status: str | None = None) -> list[dict[str, Any]]:
        """
        List table reservations, latest first.
        :param status: "confirmed", "cancelled" or "completed"
        :returns: reservations
        """
        selected = [r for r in self.reservations.values() if status is None or r.status == status]
        selected.sort(key=lambda r: r.datetime, reverse=True)
        return [to_dict(reservation) for reservation in selected]

    # Write tools -----------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_to_cart(self, item_id: str, quantity: int = 1) -> dict[str, Any]:
        """
        Add a menu item to the cart. The cart can hold items from one restaurant only.
        :param item_id: the menu item ID
        :param quantity: how many to add
        :returns: the cart
        """
        if quantity <= 0:
            raise ValueError("quantity must be at least 1")
        restaurant, item = self._menu_item(item_id)
        if self.cart and self.cart_restaurant_id != restaurant.restaurant_id:
            raise ValueError(
                f"The cart has items from another restaurant; clear the cart before ordering from {restaurant.name}"
            )
        if not item["available"]:
            raise ValueError(f"{item['name']} is currently unavailable")
        self.cart_restaurant_id = restaurant.restaurant_id
        self.cart[item_id] = self.cart.get(item_id, 0) + quantity
        return {"restaurant_id": self.cart_restaurant_id, "items": dict(self.cart)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_from_cart(self, item_id: str, quantity: int = 1) -> dict[str, Any]:
        """
        Remove a quantity of a menu item from the cart.
        :param item_id: the menu item ID
        :param quantity: how many to remove
        :returns: the cart
        """
        if item_id not in self.cart:
            raise ValueError(f"Item {item_id} is not in the cart")
        if quantity <= 0 or quantity > self.cart[item_id]:
            raise ValueError(f"quantity must be between 1 and {self.cart[item_id]}")
        self.cart[item_id] -= quantity
        if self.cart[item_id] == 0:
            del self.cart[item_id]
        if not self.cart:
            self.cart_restaurant_id = None
        return {"restaurant_id": self.cart_restaurant_id, "items": dict(self.cart)}

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def clear_cart(self) -> str:
        """
        Empty the cart.
        :returns: confirmation
        """
        self.cart, self.cart_restaurant_id = {}, None
        return "Cart cleared"

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def place_order(
        self,
        address_id: str,
        payment: str,
        coupon_code: str | None = None,
        delivery_instructions: str = "",
    ) -> dict[str, Any]:
        """
        Order everything in the cart for delivery.
        :param address_id: delivery address ID from list_addresses
        :param payment: PaySetu source_id to pay with, or "cod" for cash on delivery
        :param coupon_code: optional coupon
        :param delivery_instructions: optional note for the delivery partner
        :returns: the new order
        """
        self.address(self.addresses, address_id)
        bill = self._bill(coupon_code)
        restaurant = self._restaurant(bill["restaurant_id"])
        if not self._is_open(restaurant, self.now()):
            raise ValueError(f"{restaurant.name} is closed right now")
        if payment == COD and bill["total"] >= COD_BELOW:
            raise ValueError(f"Cash on delivery is not allowed for orders of {COD_BELOW} rupees or more")
        order_id = self.next_id("TD-ORD")
        txn_id = (
            None if payment == COD else self.charge(bill["total"], payment, "food", order_id, merchant=restaurant.name)
        )
        if bill["coupon_code"]:
            self.coupons[bill["coupon_code"]].uses_left -= 1
        order = FoodOrder(
            order_id=order_id,
            restaurant_id=restaurant.restaurant_id,
            items=bill["items"],
            item_total=bill["item_total"],
            delivery_fee=bill["delivery_fee"],
            platform_fee=bill["platform_fee"],
            packaging_fee=bill["packaging_fee"],
            gst=bill["gst"],
            discount=bill["discount"],
            total=bill["total"],
            coupon_code=bill["coupon_code"],
            address_id=address_id,
            payment=payment,
            txn_id=txn_id,
            delivery_instructions=delivery_instructions,
            placed_at=self.now_str(),
            expected_delivery_at=format_datetime(self.now() + timedelta(minutes=restaurant.delivery_time_min)),
        )
        self.orders[order_id] = order
        self.cart, self.cart_restaurant_id = {}, None
        return to_dict(order)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """
        Cancel an order before the restaurant starts preparing it. Prepaid orders are refunded in full.
        :param order_id: the order ID
        :returns: the refund amount and the updated order
        """
        order = self._order(order_id)
        if order.status != "placed":
            raise ValueError(f"Order {order_id} cannot be cancelled, current status: {order.status}")
        refund = 0
        if order.payment != COD:
            refund = order.total
            self.refund(order.txn_id, refund)
            order.refunded_amount = refund
        if order.coupon_code and order.coupon_code in self.coupons:
            self.coupons[order.coupon_code].uses_left += 1
        order.status = "cancelled"
        return {"refund": refund, "order": to_dict(order)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def rate_order(self, order_id: str, rating: int) -> dict[str, Any]:
        """
        Rate a delivered order from 1 to 5.
        :param order_id: the order ID
        :param rating: 1 to 5
        :returns: the updated order
        """
        order = self._order(order_id)
        if order.status != "delivered":
            raise ValueError("Only delivered orders can be rated")
        if order.rating is not None:
            raise ValueError(f"Order {order_id} is already rated {order.rating}")
        if not 1 <= rating <= 5:
            raise ValueError("rating must be between 1 and 5")
        order.rating = rating
        return to_dict(order)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def book_table(self, restaurant_id: str, datetime: str, guests: int, special_request: str = "") -> dict[str, Any]:
        """
        Reserve a table for dining out.
        :param restaurant_id: the restaurant ID
        :param datetime: reservation time, format YYYY-MM-DD HH:MM:SS
        :param guests: number of guests, 1 to 12
        :param special_request: optional note, e.g. "high chair for a child"
        :returns: the reservation
        """
        restaurant = self._restaurant(restaurant_id)
        moment = parse_datetime(datetime)
        if not restaurant.dine_in:
            raise ValueError(f"{restaurant.name} does not take table reservations")
        if not 1 <= guests <= MAX_TABLE_GUESTS:
            raise ValueError(f"guests must be between 1 and {MAX_TABLE_GUESTS}")
        if moment - self.now() < timedelta(hours=1):
            raise ValueError("Tables must be booked at least 1 hour ahead")
        if not self._within_hours(restaurant, moment):
            raise ValueError(f"{restaurant.name} is not open at {datetime}")
        reservation = Reservation(
            reservation_id=self.next_id("TD-RES"),
            restaurant_id=restaurant_id,
            datetime=datetime,
            guests=guests,
            special_request=special_request,
        )
        self.reservations[reservation.reservation_id] = reservation
        return to_dict(reservation)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_reservation(self, reservation_id: str) -> dict[str, Any]:
        """
        Cancel an upcoming table reservation.
        :param reservation_id: the reservation ID
        :returns: the updated reservation
        """
        if reservation_id not in self.reservations:
            raise ValueError(f"Reservation {reservation_id} does not exist")
        reservation = self.reservations[reservation_id]
        if reservation.status != "confirmed" or parse_datetime(reservation.datetime) <= self.now():
            raise ValueError("Only upcoming confirmed reservations can be cancelled")
        reservation.status = "cancelled"
        return to_dict(reservation)

    # Environment events -------------------------------------------------------
    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_food_order_status(self, order_id: str, status: str) -> None:
        """
        Move an order forward: placed, preparing, out_for_delivery, delivered.
        :param order_id: the order ID
        :param status: the new status
        """
        order = self._order(order_id)
        if status not in ORDER_FLOW or order.status not in ORDER_FLOW:
            raise ValueError(f"Cannot move order {order_id} from {order.status} to {status}")
        if ORDER_FLOW.index(status) <= ORDER_FLOW.index(order.status):
            raise ValueError(f"Order {order_id} is already {order.status}")
        order.status = status
        if status == "delivered":
            order.delivered_at = self.now_str()

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def set_menu_item_availability(self, item_id: str, available: bool) -> None:
        """
        Mark a dish available or unavailable.
        :param item_id: the menu item ID
        :param available: whether it can be ordered
        """
        self._menu_item(item_id)[1]["available"] = available

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def close_restaurant(self, restaurant_id: str, until: str) -> None:
        """
        Close a restaurant temporarily.
        :param restaurant_id: the restaurant ID
        :param until: reopening time, format YYYY-MM-DD HH:MM:SS
        """
        parse_datetime(until)
        self._restaurant(restaurant_id).closed_until = until

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def delay_delivery(self, order_id: str, minutes: int) -> str:
        """
        Delay an order's expected delivery time.
        :param order_id: the order ID
        :param minutes: delay in minutes
        :returns: the new expected delivery time
        """
        order = self._order(order_id)
        order.expected_delivery_at = format_datetime(
            parse_datetime(order.expected_delivery_at) + timedelta(minutes=minutes)
        )
        return order.expected_delivery_at

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def complete_reservation(self, reservation_id: str) -> None:
        """
        Mark a reservation as completed after the meal.
        :param reservation_id: the reservation ID
        """
        if reservation_id not in self.reservations:
            raise ValueError(f"Reservation {reservation_id} does not exist")
        self.reservations[reservation_id].status = "completed"
