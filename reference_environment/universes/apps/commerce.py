"""Shared shopping engine for KartBazaar (Flipkart / Amazon) and StyleGali (Myntra / Meesho).

Schema: app_schemas.md section 4. Tool names and the discount rule follow ARE's
Shopping app so agents that know it feel at home; the engine itself is separate
because ARE's version uses random IDs, float prices and a fixed status set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
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
    matches,
    page,
    parse_date,
    parse_datetime,
    round_rupees,
    to_dict,
)

ORDER_FLOW = ("placed", "shipped", "out_for_delivery", "delivered")
CANCELLABLE = ("placed", "shipped")
RETURN_POLICIES = ("refund", "exchange_only", "no_return")


@dataclass
class Product:
    product_id: str
    name: str
    brand: str
    category: str
    seller: str
    description: str
    rating: float
    review_count: int
    delivery_days: int
    cod_available: bool
    return_policy: str
    return_window_days: int
    variants: dict[str, dict[str, Any]]


@dataclass
class DiscountCode:
    code: str
    percent: float
    item_ids: list[str]
    description: str = ""


@dataclass
class ShopOrder:
    order_id: str
    items: list[dict[str, Any]]
    item_total: int
    discount: int
    delivery_fee: int
    total: int
    address_id: str
    payment: str
    placed_at: str
    expected_delivery: str
    status: str = "placed"
    discount_code: str | None = None
    txn_id: str | None = None
    delivered_at: str | None = None
    refunded_amount: int = 0
    history: list[dict[str, str]] = field(default_factory=list)


class CommerceApp(BharatApp):
    """Base engine; concrete apps set the policy constants below."""

    COD_LIMIT = 0
    DELIVERY_FEE = 0
    FREE_DELIVERY_FROM = 499
    ORDER_PREFIX = "ORD"

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self.products: dict[str, Product] = {}
        self.discount_codes: dict[str, DiscountCode] = {}
        self.addresses: dict[str, Address] = {}
        self.cart: dict[str, int] = {}
        self.wishlist: list[str] = []
        self.orders: dict[str, ShopOrder] = {}

    # State -----------------------------------------------------------------
    def get_state(self) -> dict[str, Any]:
        return {
            **self.base_state(),
            "products": dump_records(self.products),
            "discount_codes": dump_records(self.discount_codes),
            "addresses": dump_records(self.addresses),
            "cart": dict(self.cart),
            "wishlist": list(self.wishlist),
            "orders": dump_records(self.orders),
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self.load_base_state(state_dict)
        self.products = load_records(Product, state_dict.get("products", {}))
        self.discount_codes = load_records(DiscountCode, state_dict.get("discount_codes", {}))
        self.addresses = load_records(Address, state_dict.get("addresses", {}))
        self.cart = dict(state_dict.get("cart", {}))
        self.wishlist = list(state_dict.get("wishlist", []))
        self.orders = load_records(ShopOrder, state_dict.get("orders", {}))
        for product in self.products.values():
            if product.return_policy not in RETURN_POLICIES:
                raise ValueError(f"Product {product.product_id} has unknown return policy {product.return_policy}")

    # Helpers -----------------------------------------------------------------
    def _item(self, item_id: str) -> tuple[Product, dict[str, Any]]:
        for product in self.products.values():
            if item_id in product.variants:
                return product, product.variants[item_id]
        raise ValueError(f"Item {item_id} does not exist")

    def _product(self, product_id: str) -> Product:
        if product_id not in self.products:
            raise ValueError(f"Product {product_id} does not exist")
        return self.products[product_id]

    def _order(self, order_id: str) -> ShopOrder:
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} does not exist")
        return self.orders[order_id]

    def _set_status(self, order: ShopOrder, status: str) -> None:
        order.status = status
        order.history.append({"status": status, "at": self.now_str()})

    def _bill(self, discount_code: str | None) -> dict[str, Any]:
        if not self.cart:
            raise ValueError("Cart is empty")
        lines, item_total, discount = [], 0, Decimal(0)
        code = None
        if discount_code:
            code = self.discount_codes.get(discount_code.strip())
            if code is None:
                raise ValueError(f"Discount code {discount_code} does not exist")
        for item_id, quantity in self.cart.items():
            product, variant = self._item(item_id)
            if not variant["available"]:
                raise ValueError(f"{product.name} ({item_id}) is out of stock; remove it from the cart")
            if code is not None and item_id not in code.item_ids:
                raise ValueError(
                    f"Discount code {code.code} is not valid for item {item_id}; it must apply to every cart item"
                )
            line_total = variant["price"] * quantity
            item_total += line_total
            if code is not None:
                discount += Decimal(line_total) * Decimal(str(code.percent)) / Decimal(100)
            lines.append(
                {
                    "item_id": item_id,
                    "product_id": product.product_id,
                    "name": product.name,
                    "options": dict(variant.get("options", {})),
                    "quantity": quantity,
                    "price": variant["price"],
                    "return_status": "none",
                }
            )
        discount_rupees = round_rupees(discount)
        after_discount = item_total - discount_rupees
        delivery_fee = 0 if after_discount >= self.FREE_DELIVERY_FROM else self.DELIVERY_FEE
        return {
            "lines": lines,
            "item_total": item_total,
            "discount": discount_rupees,
            "delivery_fee": delivery_fee,
            "total": after_discount + delivery_fee,
            "discount_code": code.code if code else None,
        }

    def _line_refund(self, order: ShopOrder, line: dict[str, Any]) -> int:
        """What the customer paid for one line, after its share of the discount."""
        gross = line["price"] * line["quantity"]
        if not order.discount:
            return gross
        return gross - round_rupees(Decimal(order.discount) * Decimal(gross) / Decimal(order.item_total))

    def _pay_back(self, order: ShopOrder, amount: int) -> None:
        if amount <= 0:
            return
        if order.payment == COD:
            self.refund_cod(amount, order.order_id)
        else:
            self.refund(order.txn_id, amount)
        order.refunded_amount += amount

    @staticmethod
    def _summary(product: Product) -> dict[str, Any]:
        prices = [variant["price"] for variant in product.variants.values()]
        return {
            "product_id": product.product_id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "rating": product.rating,
            "min_price": min(prices) if prices else None,
            "in_stock": any(variant["available"] for variant in product.variants.values()),
        }

    # Read tools --------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_all_products(self, offset: int = 0, limit: int = 10) -> dict[str, Any]:
        """
        List all products in the catalogue.
        :param offset: index of the first product to return
        :param limit: maximum number of products to return
        :returns: a page of product summaries with the total count
        """
        return page([self._summary(p) for p in self.products.values()], offset, limit)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_product_details(self, product_id: str) -> dict[str, Any]:
        """
        Get a product with all its variants (item_id, price, availability, options such as size and colour),
        delivery time, cash-on-delivery availability and return policy.
        :param product_id: the product ID
        :returns: the product
        """
        return to_dict(self._product(product_id))

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_product(
        self,
        product_name: str,
        category: str | None = None,
        max_price: int | None = None,
        sort_by: str = "relevance",
        offset: int = 0,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Search products by name, brand or description.
        :param product_name: words to search for
        :param category: optional category filter
        :param max_price: only products with a variant at or below this price
        :param sort_by: "relevance", "price_low", "price_high" or "rating"
        :param offset: index of the first result to return
        :param limit: maximum number of results to return
        :returns: a page of product summaries with the total count
        """
        words = product_name.casefold().split()
        found = []
        for product in self.products.values():
            haystack = f"{product.name} {product.brand} {product.category} {product.description}".casefold()
            score = sum(word in haystack for word in words)
            if words and score == 0:
                continue
            if category and not matches(category, product.category):
                continue
            summary = self._summary(product)
            if max_price is not None and (summary["min_price"] is None or summary["min_price"] > max_price):
                continue
            found.append((score, summary))
        orders = {
            "relevance": lambda pair: (-pair[0], pair[1]["product_id"]),
            "price_low": lambda pair: (pair[1]["min_price"], pair[1]["product_id"]),
            "price_high": lambda pair: (-pair[1]["min_price"], pair[1]["product_id"]),
            "rating": lambda pair: (-pair[1]["rating"], pair[1]["product_id"]),
        }
        if sort_by not in orders:
            raise ValueError("sort_by must be relevance, price_low, price_high or rating")
        found.sort(key=orders[sort_by])
        return page([summary for _, summary in found], offset, limit)

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_cart(self) -> dict[str, Any]:
        """
        Show the cart with each item's price and quantity.
        :returns: cart lines and the item total before discounts and delivery
        """
        lines = []
        for item_id, quantity in self.cart.items():
            product, variant = self._item(item_id)
            lines.append(
                {
                    "item_id": item_id,
                    "name": product.name,
                    "options": variant.get("options", {}),
                    "price": variant["price"],
                    "quantity": quantity,
                    "available": variant["available"],
                }
            )
        return {"items": lines, "item_total": sum(line["price"] * line["quantity"] for line in lines)}

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_all_discount_codes(self) -> dict[str, list[str]]:
        """
        List every discount code with the item IDs it applies to.
        :returns: mapping of discount code to item IDs
        """
        return {code.code: list(code.item_ids) for code in self.discount_codes.values()}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_discount_code_info(self, discount_code: str) -> dict[str, float]:
        """
        Show which items a discount code applies to and its percentage.
        A code can be used at checkout only if it applies to every item in the cart.
        :param discount_code: the code
        :returns: mapping of item ID to discount percentage
        """
        code = self.discount_codes.get(discount_code.strip())
        return {item_id: code.percent for item_id in code.item_ids} if code else {}

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_orders(self) -> list[dict[str, Any]]:
        """
        List all orders, newest first.
        :returns: orders with status and totals
        """
        selected = sorted(self.orders.values(), key=lambda o: (o.placed_at, o.order_id), reverse=True)
        return [to_dict(order) for order in selected]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_order_details(self, order_id: str) -> dict[str, Any]:
        """
        Get an order with its items, bill, address, payment and status.
        :param order_id: the order ID
        :returns: the order
        """
        return to_dict(self._order(order_id))

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def track_order(self, order_id: str) -> dict[str, Any]:
        """
        Track an order's delivery.
        :param order_id: the order ID
        :returns: current status, expected delivery date and status history
        """
        order = self._order(order_id)
        return {
            "order_id": order.order_id,
            "status": order.status,
            "expected_delivery": order.expected_delivery,
            "delivered_at": order.delivered_at,
            "history": list(order.history),
        }

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_wishlist(self) -> list[dict[str, Any]]:
        """
        List wishlisted items with current price and availability.
        :returns: wishlist items
        """
        listed = []
        for item_id in self.wishlist:
            product, variant = self._item(item_id)
            listed.append(
                {
                    "item_id": item_id,
                    "product_id": product.product_id,
                    "name": product.name,
                    "options": variant.get("options", {}),
                    "price": variant["price"],
                    "available": variant["available"],
                }
            )
        return listed

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_addresses(self) -> list[dict[str, Any]]:
        """
        List saved delivery addresses.
        :returns: addresses
        """
        return [to_dict(address) for address in self.addresses.values()]

    # Write tools -----------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_to_cart(self, item_id: str, quantity: int = 1) -> dict[str, int]:
        """
        Add an item (a specific variant, e.g. a size) to the cart.
        :param item_id: the variant's item ID from get_product_details
        :param quantity: how many to add
        :returns: the cart as item ID to quantity
        """
        if quantity <= 0:
            raise ValueError("quantity must be at least 1")
        product, variant = self._item(item_id)
        if not variant["available"]:
            raise ValueError(f"{product.name} ({item_id}) is out of stock")
        self.cart[item_id] = self.cart.get(item_id, 0) + quantity
        return dict(self.cart)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_from_cart(self, item_id: str, quantity: int = 1) -> dict[str, int]:
        """
        Remove a quantity of an item from the cart.
        :param item_id: the item ID
        :param quantity: how many to remove
        :returns: the cart as item ID to quantity
        """
        if item_id not in self.cart:
            raise ValueError(f"Item {item_id} is not in the cart")
        if quantity <= 0 or quantity > self.cart[item_id]:
            raise ValueError(f"quantity must be between 1 and {self.cart[item_id]}")
        self.cart[item_id] -= quantity
        if self.cart[item_id] == 0:
            del self.cart[item_id]
        return dict(self.cart)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def checkout(self, address_id: str, payment: str, discount_code: str | None = None) -> dict[str, Any]:
        """
        Place an order for everything in the cart.
        :param address_id: delivery address ID from list_addresses
        :param payment: PaySetu source_id to pay with, or "cod" for cash on delivery
        :param discount_code: optional code; it must apply to every item in the cart
        :returns: the new order
        """
        if address_id not in self.addresses:
            raise ValueError(f"Address {address_id} does not exist")
        bill = self._bill(discount_code)
        if payment == COD:
            if not all(self._item(line["item_id"])[0].cod_available for line in bill["lines"]):
                raise ValueError("Cash on delivery is not available for every item in the cart")
            if bill["total"] > self.COD_LIMIT:
                raise ValueError(f"Cash on delivery is allowed only up to {self.COD_LIMIT} rupees")
        order_id = self.next_id(self.ORDER_PREFIX, 5)
        txn_id = None if payment == COD else self.charge(bill["total"], payment, "shopping", order_id)
        delivery_days = max(self._item(line["item_id"])[0].delivery_days for line in bill["lines"])
        order = ShopOrder(
            order_id=order_id,
            items=bill["lines"],
            item_total=bill["item_total"],
            discount=bill["discount"],
            delivery_fee=bill["delivery_fee"],
            total=bill["total"],
            discount_code=bill["discount_code"],
            address_id=address_id,
            payment=payment,
            txn_id=txn_id,
            placed_at=self.now_str(),
            expected_delivery=(self.today() + timedelta(days=delivery_days)).isoformat(),
        )
        order.history.append({"status": "placed", "at": order.placed_at})
        self.orders[order_id] = order
        self.cart = {}
        return to_dict(order)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """
        Cancel an order that has not gone out for delivery. Prepaid orders are refunded in full.
        :param order_id: the order ID
        :returns: the refund amount and the updated order
        """
        order = self._order(order_id)
        if order.status not in CANCELLABLE:
            raise ValueError(f"Order {order_id} cannot be cancelled, current status: {order.status}")
        refund = 0 if order.payment == COD else order.total
        if refund:
            self.refund(order.txn_id, refund)
            order.refunded_amount += refund
        self._set_status(order, "cancelled")
        return {"refund": refund, "order": to_dict(order)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def request_return(self, order_id: str, item_id: str, reason: str) -> dict[str, Any]:
        """
        Request a return and refund of one delivered item. Allowed only within the product's return window
        and only for products whose return policy is "refund".
        :param order_id: the order ID
        :param item_id: the item ID within the order
        :param reason: why the item is being returned
        :returns: the updated order
        """
        order = self._order(order_id)
        line = next((line for line in order.items if line["item_id"] == item_id), None)
        if line is None:
            raise ValueError(f"Item {item_id} is not in order {order_id}")
        if order.delivered_at is None:
            raise ValueError("Only delivered items can be returned")
        if line["return_status"] != "none":
            raise ValueError(f"A return for item {item_id} already exists ({line['return_status']})")
        product = self._product(line["product_id"])
        if product.return_policy != "refund":
            raise ValueError(f"{product.name} cannot be returned for a refund (policy: {product.return_policy})")
        last_day = parse_datetime(order.delivered_at).date() + timedelta(days=product.return_window_days)
        if self.today() > last_day:
            raise ValueError(f"The return window for {product.name} closed on {last_day.isoformat()}")
        line["return_status"] = "requested"
        line["return_reason"] = reason
        self._set_status(order, "return_requested")
        return to_dict(order)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_to_wishlist(self, item_id: str) -> list[str]:
        """
        Add an item to the wishlist.
        :param item_id: the item ID
        :returns: wishlist item IDs
        """
        self._item(item_id)
        if item_id in self.wishlist:
            raise ValueError(f"Item {item_id} is already in the wishlist")
        self.wishlist.append(item_id)
        return list(self.wishlist)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_from_wishlist(self, item_id: str) -> list[str]:
        """
        Remove an item from the wishlist.
        :param item_id: the item ID
        :returns: wishlist item IDs
        """
        if item_id not in self.wishlist:
            raise ValueError(f"Item {item_id} is not in the wishlist")
        self.wishlist.remove(item_id)
        return list(self.wishlist)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_address(self, label: str, line1: str, area: str, city: str, pincode: str, phone: str) -> str:
        """
        Save a delivery address.
        :param label: one of home, office, brother, in_laws, other
        :param line1: flat or house number and street
        :param area: locality
        :param city: city
        :param pincode: 6-digit PIN code
        :param phone: contact phone number for delivery
        :returns: the address ID
        """
        return self.save_address(self.addresses, f"{self.ORDER_PREFIX}-ADDR", label, line1, area, city, pincode, phone)

    # Environment events -------------------------------------------------------
    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_order_status(self, order_id: str, status: str) -> None:
        """
        Move an order forward: placed, shipped, out_for_delivery, delivered.
        :param order_id: the order ID
        :param status: the new status
        """
        order = self._order(order_id)
        if status not in ORDER_FLOW or order.status not in ORDER_FLOW:
            raise ValueError(f"Cannot move order {order_id} from {order.status} to {status}")
        if ORDER_FLOW.index(status) <= ORDER_FLOW.index(order.status):
            raise ValueError(f"Order {order_id} is already {order.status}")
        self._set_status(order, status)
        if status == "delivered":
            order.delivered_at = self.now_str()

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def delay_delivery(self, order_id: str, expected_delivery: str) -> None:
        """
        Push an order's expected delivery date.
        :param order_id: the order ID
        :param expected_delivery: new expected date, format YYYY-MM-DD
        """
        parse_date(expected_delivery)
        self._order(order_id).expected_delivery = expected_delivery

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def set_item_availability(self, item_id: str, available: bool) -> None:
        """
        Mark an item in or out of stock.
        :param item_id: the item ID
        :param available: whether it can be bought
        """
        self._item(item_id)[1]["available"] = available

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_item_price(self, item_id: str, price: int) -> None:
        """
        Change an item's price.
        :param item_id: the item ID
        :param price: new price in rupees
        """
        if price <= 0:
            raise ValueError("price must be positive")
        self._item(item_id)[1]["price"] = price

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def complete_return(self, order_id: str, item_id: str) -> int:
        """
        The courier picks up a returned item and the refund is issued.
        :param order_id: the order ID
        :param item_id: the item ID
        :returns: the refunded amount
        """
        order = self._order(order_id)
        line = next((line for line in order.items if line["item_id"] == item_id), None)
        if line is None or line["return_status"] != "requested":
            raise ValueError(f"No open return for item {item_id} in order {order_id}")
        amount = self._line_refund(order, line)
        self._pay_back(order, amount)
        line["return_status"] = "refunded"
        all_returned = all(item["return_status"] == "refunded" for item in order.items)
        any_open = any(item["return_status"] == "requested" for item in order.items)
        self._set_status(order, "returned" if all_returned else ("return_requested" if any_open else "delivered"))
        return amount


class KartBazaarApp(CommerceApp):
    """
    KartBazaar is a general online store: electronics, home, groceries and party supplies.

    Notes:
        - Products have variants (sizes, colours, pack sizes); add the variant's item_id to the cart.
        - A discount code can be used at checkout only if it applies to every item in the cart.
        - Delivery is free from 499 rupees (after discount), otherwise 40 rupees.
        - Cash on delivery ("cod") is allowed when every item supports it and the total is at most 5000 rupees.
        - Orders can be cancelled while placed or shipped. Delivered items can be returned for a refund within
          their return window if their return policy is "refund". Refunds go back to the PaySetu source that paid;
          cash-on-delivery refunds go to the default bank account.
        - Amounts are whole rupees and times are local (IST).
    """

    COD_LIMIT = 5000
    DELIVERY_FEE = 40
    ORDER_PREFIX = "KB"

    def __init__(self, name: str | None = "KartBazaar") -> None:
        super().__init__(name)


class StyleGaliApp(CommerceApp):
    """
    StyleGali is a fashion and value store: clothing, footwear, accessories and home decor.

    Notes:
        - Products have variants (sizes, colours); add the variant's item_id to the cart.
        - A discount code can be used at checkout only if it applies to every item in the cart.
        - Delivery is free from 499 rupees (after discount), otherwise 69 rupees.
        - Cash on delivery ("cod") is allowed when every item supports it and the total is at most 3000 rupees.
        - Orders can be cancelled while placed or shipped. Delivered items can be returned for a refund within
          their return window if their return policy is "refund"; "exchange_only" items cannot be refunded.
          Refunds go back to the PaySetu source that paid; cash-on-delivery refunds go to the default bank account.
        - Amounts are whole rupees and times are local (IST).
    """

    COD_LIMIT = 3000
    DELIVERY_FEE = 69
    ORDER_PREFIX = "SG"

    def __init__(self, name: str | None = "StyleGali") -> None:
        super().__init__(name)
