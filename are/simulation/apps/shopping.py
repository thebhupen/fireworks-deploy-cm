# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypedDict

from are.simulation.tool_utils import OperationType


class ProductMetadata(TypedDict):
    range: tuple[int, int]  # (start_index, end_index)
    total: int  # Total number of products


class ProductListResult(TypedDict):
    products: dict[str, str]  # Maps product names to product IDs
    metadata: ProductMetadata  # Contains range and total information


import logging

from are.simulation.apps.app import App
from are.simulation.tool_utils import app_tool, data_tool, env_tool
from are.simulation.types import EventType, disable_events, event_registered
from are.simulation.utils import get_state_dict, serialize_field, type_check

logger = logging.getLogger(__name__)


@dataclass
class Item:
    price: float
    available: bool = True
    item_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    options: dict[str, Any] = field(default_factory=dict)

    def load_state(self, state_dict: dict[str, Any]):
        self.price = state_dict["price"]
        self.available = state_dict["available"]
        self.item_id = state_dict["item_id"]
        self.options = state_dict["options"]


@dataclass
class Product:
    name: str
    product_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    variants: dict[str, Item] = field(default_factory=dict)

    def load_state(self, state_dict: dict[str, Any]):
        self.name = state_dict["name"]
        self.product_id = state_dict["product_id"]
        for v in state_dict["variants"]:
            item = Item(
                price=state_dict["variants"][v]["price"],
                available=state_dict["variants"][v]["available"],
                item_id=state_dict["variants"][v]["item_id"],
            )
            item.load_state(state_dict["variants"][v])
            self.variants[v] = item


@dataclass
class CartItem:
    item_id: str
    quantity: int
    price: float
    available: bool = True
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class Order:
    order_status: str
    order_date: Any
    order_total: float
    order_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    order_items: dict[str, CartItem] = field(default_factory=dict)

    def load_state(self, state_dict: dict[str, Any]):
        self.order_status = state_dict["order_status"]
        # Handle order_date which could be a datetime object or an ISO format string
        if isinstance(state_dict["order_date"], str):
            try:
                self.order_date = datetime.fromisoformat(state_dict["order_date"])
            except ValueError:
                # If it's not a valid ISO format string, keep it as is
                self.order_date = state_dict["order_date"]
        else:
            self.order_date = state_dict["order_date"]
        self.order_total = state_dict["order_total"]
        self.order_id = state_dict["order_id"]
        for item in state_dict["order_items"]:
            self.order_items[item] = CartItem(**state_dict["order_items"][item])


@dataclass
class ShoppingApp(App):
    """
    A shopping application that facilitates the management of a product catalog, user cart, and orders.
    This class provides core functionality for browsing products, adding items to a cart, applying discount
    codes, and managing orders. It also includes utility methods for loading data from files, saving
    application state, and restoring state as needed.

    The ShoppingApp maintains a catalog of products, where each product can have multiple variants,
    and tracks each user's cart and orders individually. Products and variants are identified by unique
    product IDs and item IDs, respectively.

    Key Features:
        - Product Management: Load, browse, and retrieve detailed product information
        - Cart Management: Add, update, and remove items from the cart
        - Order Processing: Create, list, retrieve, and manage orders
        - Discount Codes: Apply discount codes to items in the cart and track their usage
        - State Management: Save and load application state from files and dictionaries

    Notes:
        - All datetime operations are in UTC and managed by a global time manager
        - Unique IDs for products, items, and orders are generated automatically
        - Discount codes apply on a per-item basis and are checked for validity before use
        - Products in the cart are automatically removed upon successful checkout
        - Orders cannot be canceled if marked as "delivered" or "cancelled"
    """

    name: str | None = None
    # database of all products - product_id is the key and the value is the product
    products: dict[str, Product] = field(default_factory=dict)
    # user cart item_id -> CartItem
    cart: dict[str, CartItem] = field(default_factory=dict)
    # user orders (ongoing and completed)
    orders: dict[str, Order] = field(default_factory=dict)
    # available discount codes - item_id is the key and the value is discount codes that works for this item
    # Note that the key is the item_id, not the product_id.
    # Each discount code is a dictionary with key being the code and value the discount percentage.
    discount_codes: dict[str, dict[str, float]] = field(default_factory=dict)

    def __post_init__(self):
        super().__init__(self.name)

    def get_state(self) -> dict[str, Any] | None:
        state = get_state_dict(self, ["products", "cart", "discount_codes"])

        # Serialize orders with datetime objects converted to ISO format strings
        serialized_orders = {}
        for order_id, order in self.orders.items():
            order_dict = serialize_field(order)
            # Convert order_date to ISO format string if it's a datetime object
            if isinstance(order_dict["order_date"], datetime):
                order_dict["order_date"] = order_dict["order_date"].isoformat()
            serialized_orders[order_id] = order_dict

        state["orders"] = serialized_orders
        return state

    def load_state(self, state_dict: dict[str, Any]):
        self.load_products_from_dict(state_dict["products"])
        self.load_discount_codes_from_dict(state_dict["discount_codes"])
        self.load_cart_from_dict(state_dict["cart"])
        self.load_orders_from_dict(state_dict["orders"])

    def load_products_from_file(self, path):
        try:
            with open(path) as f:
                products_dict = json.load(f)
                self.load_products_from_dict(products_dict)
        except Exception as e:
            logger.exception(e)

    def load_products_from_dict(self, products):
        for p in products:
            product = Product(
                name=products[p]["name"],
                product_id=products[p]["product_id"],
            )
            product.load_state(products[p])
            self.products[p] = product

    def load_discount_codes_from_dict(self, discount_codes):
        try:
            self.discount_codes.update(discount_codes)
        except Exception as e:
            logger.exception(e)

    def load_cart_from_dict(self, cart):
        for item_id in cart:
            self.cart[item_id] = CartItem(**cart[item_id])

    def load_orders_from_dict(self, orders):
        for order_id in orders:
            # Handle order_date which could be a datetime object or an ISO format string
            order_date = orders[order_id]["order_date"]
            if isinstance(order_date, str):
                try:
                    order_date = datetime.fromisoformat(order_date)
                except ValueError:
                    # If it's not a valid ISO format string, keep it as is
                    pass

            order = Order(
                order_status=orders[order_id]["order_status"],
                order_date=order_date,
                order_total=orders[order_id]["order_total"],
                order_id=orders[order_id]["order_id"],
            )
            order.load_state(orders[order_id])
            self.orders[order_id] = order

    def reset(self):
        super().reset()
        self.products = {}
        self.cart = {}
        self.orders = {}
        self.discount_codes = {}

    def _get_item(self, item_id: str) -> dict:
        """
        given an item_id, return the item details
        """
        for product_id in self.products:
            for it_id in self.products[product_id].variants:
                if it_id == item_id:
                    return {
                        "name": self.products[product_id].name,
                        "product_id": product_id,
                        **serialize_field(self.products[product_id].variants[item_id]),
                    }
        return {}

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_product(self, name: str) -> str:
        """
        Add a product to the catalog. The created product currently doesn't have any items. Please add items to the product using the add_item_to_product tool.
        :param name: name of the product
        :return: product id if successful, otherwise raise ValueError.
        """
        product_id: str = uuid.uuid4().hex
        if product_id in self.products:
            raise ValueError("Product already exists")
        self.products[product_id] = Product(name=name, product_id=product_id)
        return product_id

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_item_to_product(
        self,
        product_id: str,
        price: float,
        options: dict[str, Any] = {},
        available: bool = True,
    ) -> str:
        """
        Add an item variant to a product.
        :param product_id: product id
        :param price: price of the item
        :param options: characteristics of the item. Example: {"color": "red", "size": "large"}.
        :param available: whether the item is available
        :return: item id if successful, otherwise raise ValueError.
        """
        item_id: str = uuid.uuid4().hex
        if product_id not in self.products:
            raise ValueError("Product does not exist")
        self.products[product_id].variants[item_id] = Item(
            item_id=item_id,
            options=options,
            available=available,
            price=price,
        )
        return item_id

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_item(
        self,
        item_id: str,
        new_price: float | None = None,
        new_availability: bool | None = None,
    ) -> str:
        """
        Update an item in the catalog with new price and/or new availability
        :param item_id: item id
        :param new_price: new price of the item
        :param new_availability: new availability of the item
        :return: item id if successful, otherwise raise ValueError.
        """
        if new_price is None and new_availability is None:
            raise ValueError("No update provided")

        for product_id in self.products:
            for it_id in self.products[product_id].variants:
                if it_id == item_id:
                    item = self.products[product_id].variants[item_id]
                    if new_price is not None:
                        item.price = new_price
                    if new_availability is not None:
                        item.available = new_availability
                    self.products[product_id].variants[item_id] = item
                    return item_id
        raise ValueError(f"Item with id {item_id} does not exist")

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_discount_code(self, item_id: str, discount_code: dict[str, float]) -> str:
        """
        Add a discount code to the inventory.
        :param item_id: item id of the item for which this discount code works
        :param discount_code: discount code is the dictionary with key being the code and value the discount percentage.
        :return: success message if successful, otherwise raise ValueError.
        """
        found = False
        for item in self.products:
            if item_id in self.products[item].variants:
                found = True
                break

        if found is False:
            raise ValueError(f"Item {item_id} does not exist in the inventory.")

        if item_id not in self.discount_codes:
            self.discount_codes[item_id] = {}
        self.discount_codes[item_id].update(discount_code)
        return "Successfully added the discount code"

    @type_check
    @data_tool()
    def add_order(
        self,
        order_id: str,
        order_status: str,
        order_date: float,
        order_total: float,
        item_id: str,
        quantity: int,
    ) -> str:
        """
        Add an order to the orders.
        :param order_id: order id to add to orders
        :param order_status: order status to add to orders
        :param order_date: date of the order
        :param order_total: total price of the order
        :param item_id: item id ordered
        :param quantity: quantity of the item ordered
        :return: order id if successful, otherwise raise ValueError.
        """
        item_dict = self._get_item(item_id)
        if len(item_dict) == 0:
            raise ValueError("Item does not exist")

        self.orders[order_id] = Order(
            order_status=order_status,
            order_date=order_date,
            order_total=order_total,
            order_id=order_id,
            order_items={item_id: CartItem(**item_dict, quantity=quantity)},
        )
        return order_id

    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_all_products(self, offset: int = 0, limit: int = 10) -> ProductListResult:
        """
        List all products in the catalog.
        :param offset: offset to start listing from, default is 0.
        :param limit: number of products to list, default is 10.
        :returns: product details, dictionary of name to product_id, limited to the specified offset and limit, with additional metadata about the range of products retrieved and total number of products.
        """
        products = self.products
        product_dict = {
            product.name: product.product_id for product in products.values()
        }
        start_index = offset
        end_index = offset + limit
        product_dict = dict(sorted(product_dict.items())[start_index:end_index])
        return {
            "products": product_dict,
            "metadata": {
                "range": (
                    offset,
                    min(offset + limit, len(list(products.values()))),
                ),
                "total": len(list(products.values())),
            },
        }

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_product_details(self, product_id: str) -> Product:
        """
        Get product details for a given product id.
        :param product_id: product id to get details for
        :returns: product details
        """
        if product_id not in self.products:
            raise ValueError("Product does not exist")
        return self.products[product_id]

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_product(
        self, product_name: str, offset: int = 0, limit: int = 10
    ) -> list[Product]:
        """
        Search for a product in the inventory by its name.
        :param product_name: Name of the product to search for.
        :param offset: offset to start listing from, default is 0.
        :param limit: number of products to list, default is 10.
        :returns: List of products with the given name, limited to the specified offset and limit.
        """
        all_products = list(self.products.values())
        names = []
        product_name_to_id = {}
        for p in all_products:
            names.append(p.name)
            product_name_to_id[p.name] = p.product_id

        ret_products = []
        for name in names:
            if product_name.lower() in name.lower():
                ret_products.append(self.products[product_name_to_id[name]])

        start_index = offset
        end_index = offset + limit
        ret_products = ret_products[start_index:end_index]

        return ret_products

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_to_cart(self, item_id: str, quantity: int = 1) -> str:
        """
        Add item to cart.
        :param item_id: item id to add to cart
        :param quantity: quantity to add to cart, default is 1
        :returns: item id of the added item if successful, otherwise raise Exception.
        """
        if quantity <= 0:
            raise ValueError("Quantity cannot be negative or zero")
        item = self._get_item(item_id)
        if not item:
            raise ValueError("Product does not exist")
        if not item["available"]:
            raise ValueError("Product is not available")

        if item_id not in self.cart:
            self.cart[item_id] = CartItem(
                price=item["price"],
                item_id=item["item_id"],
                quantity=quantity,
                available=item["available"],
                options=item["options"],
            )
        else:
            self.cart[item_id].quantity += quantity

        return item_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_from_cart(self, item_id: str, quantity: int = 1) -> str:
        """
        Remove item from cart.
        :param item_id: item id to remove from cart
        :param quantity: quantity to remove from cart
        :returns: item id of the removed item if successful, otherwise raise Exception.
        """
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if item_id not in self.cart:
            raise ValueError("Product not in cart")
        if quantity > self.cart[item_id].quantity:
            raise ValueError("Quantity exceeds available quantity")
        self.cart[item_id].quantity -= quantity
        if self.cart[item_id].quantity == 0:
            del self.cart[item_id]
        return item_id

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_cart(self) -> dict[str, Any]:
        """
        List cart contents.
        :returns: cart contents
        """
        return self.cart

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def checkout(self, discount_code: str | None = None) -> str:
        """
        Checkout the order and create a new order from the current cart contents.

        IMPORTANT: If a discount code is provided, it MUST be valid for ALL items in the cart.
        The checkout will fail with a ValueError if ANY item in the cart does not support
        the provided discount code. This is a strict all-or-nothing discount policy.

        :param discount_code: Optional discount code to apply to the entire order.
                            If provided, this discount code must be available for every
                            single item in the cart, otherwise the entire checkout will
                            fail with an error. If you want to use a discount code,
                            ensure all items in your cart support that specific code.
        :returns: order id of the created order if successful, otherwise raise Exception.
        :raises ValueError: If discount code is not valid for any item in the cart
        :raises Exception: If cart is empty
        """
        if not self.cart:
            raise Exception("Cart is empty")

        order_total = 0
        for item_id in self.cart:
            discount_percentage = 0
            if discount_code is not None and len(discount_code) > 0:
                if item_id not in self.discount_codes:
                    raise ValueError(
                        "There is no valid discount codes for the item with id - {}".format(
                            item_id
                        )
                    )
                elif discount_code not in self.discount_codes[item_id]:
                    raise ValueError(
                        "The provided discount code is not valid for the item with id - {}".format(
                            item_id
                        )
                    )
                else:
                    discount_percentage = self.discount_codes[item_id][discount_code]
            order_total += (
                self.cart[item_id].price
                * self.cart[item_id].quantity
                * (1 - discount_percentage / 100)
            )

        new_order_dict = {
            "order_id": uuid.uuid4().hex,
            "order_status": "processed",
            "order_date": datetime.fromtimestamp(
                self.time_manager.time(), tz=timezone.utc
            ),
            "order_total": order_total,
            "order_items": self.cart,
        }
        new_order = Order(**new_order_dict)
        self.orders[new_order_dict["order_id"]] = new_order
        self.cart = {}
        return new_order.order_id

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_discount_code_info(self, discount_code: str = "") -> dict[str, float]:
        """
        Takes the discount code and returns the applicable items with their discount percentages.
        :param discount_code: discount code to check
        :returns: Dictionary mapping item_id to discount_percentage for items that support this discount code
        """
        result = {}
        for item_id in self.discount_codes:
            if discount_code in self.discount_codes[item_id]:
                result[item_id] = self.discount_codes[item_id][discount_code]
        return result

    @app_tool()
    @data_tool()
    def get_all_discount_codes(self) -> dict[str, list[str]]:
        """
        Returns all the discount codes that are available with the items they apply to.
        :returns: Dictionary mapping discount codes to list of item IDs they apply to
        """
        result = {}
        for item_id in self.discount_codes:
            for code in self.discount_codes[item_id]:
                if code not in result:
                    result[code] = []
                result[code].append(item_id)
        return result

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_orders(self) -> dict[str, Order]:
        """
        List all orders.
        :returns: orders, dictionary of order_id to order details
        """
        return self.orders

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_order_details(self, order_id: str) -> Order:
        """
        Get order details.
        :param order_id: order id to get details for
        :returns: order details if successful, otherwise raise Exception.
        """
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        return self.orders[order_id]

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_order_status(self, order_id: str, status: str = "shipped") -> None:
        """
        Update order status.
        :param order_id: order id to update status for
        :param status: status to update to, default is "shipped". Valid values are "processed", "shipped", "delivered", "cancelled".
        :returns: None if successful, otherwise raise Exception.
        """
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        if status not in ["processed", "shipped", "delivered", "cancelled"]:
            raise ValueError("Invalid status")
        self.orders[order_id].order_status = status

    @type_check
    @app_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_order(self, order_id: str) -> str:
        """
        Cancel an order that is not yet delivered.
        :param order_id: order id to cancel
        :returns: order id if successful, otherwise raise Exception.
        """
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        if self.orders[order_id].order_status not in ["processed", "shipped"]:
            raise ValueError(
                f"Order {order_id} cannot be cancelled, current status: {self.orders[order_id].order_status}"
            )
        with disable_events():
            self.update_order_status(order_id, "cancelled")
        return order_id


@dataclass
class Shopping(ShoppingApp):
    __doc__ = ShoppingApp.__doc__

    name: str | None = "Shopping"
