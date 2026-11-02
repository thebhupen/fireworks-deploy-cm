# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import os

import pytest

from are.simulation.apps.shopping import ShoppingApp
from are.simulation.dataset_helpers import get_data_path
from are.simulation.environment import Environment
from are.simulation.tests.utils import IN_GITHUB_ACTIONS

dummy_data = {
    "6938111410": {
        "name": "Running Shoes",
        "product_id": "6938111410",
        "variants": {
            "4153505238": {
                "item_id": "4153505238",
                "options": {
                    "size": "8",
                    "color": "red",
                    "material": "leather",
                    "sole": "EVA",
                },
                "available": True,
                "price": 158.67,
            },
            "1775591963": {
                "item_id": "1775591963",
                "options": {
                    "size": "10",
                    "color": "white",
                    "material": "leather",
                    "sole": "EVA",
                },
                "available": True,
                "price": 154.75,
            },
        },
    },
    "8310926033": {
        "name": "Water Bottle",
        "product_id": "8310926033",
        "variants": {
            "1434748144": {
                "item_id": "1434748144",
                "options": {"capacity": "1000ml", "material": "glass", "color": "red"},
                "available": False,
                "price": 49.72,
            },
            "4579334072": {
                "item_id": "4579334072",
                "options": {"capacity": "750ml", "material": "glass", "color": "black"},
                "available": True,
                "price": 54.85,
            },
        },
    },
}

dummy_discount_codes = {
    "4579334072": {"DISC10": 10, "DISC20": 20},
    "1775591963": {"DISC10": 10},
}


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="does not work in github actions")
def test_shopping_init_from_file():
    app = ShoppingApp()
    path_to_products = os.path.join(get_data_path(), "shopping/products.json")
    app.load_products_from_file(path_to_products)

    environment = Environment()
    environment.register_apps([app])
    assert app.products is not None


def test_shopping_init_from_dict():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    assert app.products is not None


def test_list_all_products():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    products = app.list_all_products()
    assert products is not None
    assert "Running Shoes" in products["products"]
    assert "Water Bottle" in products["products"]


def test_get_product_details():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    product_details = app.get_product_details("6938111410")
    assert product_details is not None
    assert product_details.name == "Running Shoes"
    assert product_details.product_id == "6938111410"
    assert product_details.variants is not None
    with pytest.raises(ValueError):
        app.get_product_details("1234567890")


def test_add_to_cart_default():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 2)
    assert app.cart is not None
    assert len(app.cart) == 1
    assert app.cart["4153505238"].quantity == 2


def test_add_to_cart_unexisting_item():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    with pytest.raises(ValueError):
        app.add_to_cart("123", 2)
    assert app.cart.get("123") is None


def test_add_to_cart_unavailable_item():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    with pytest.raises(ValueError):
        app.add_to_cart("1434748144", 1)


def test_remove_from_cart():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    app.remove_from_cart("4153505238", 2)
    assert app.cart is not None
    assert len(app.cart) == 1
    assert app.cart["4153505238"].quantity == 3


def test_remove_from_cart_exceed_quantity():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    with pytest.raises(ValueError):
        app.remove_from_cart("4153505238", 7)
    assert app.cart is not None
    assert len(app.cart) == 1
    assert app.cart["4153505238"].quantity == 5
    with pytest.raises(ValueError):
        app.remove_from_cart("5678987432", 2)


def test_checkout():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    app.add_to_cart("4579334072", 1)
    app.checkout()

    assert app.orders is not None
    assert len(app.orders) == 1
    order_key = list(app.orders.keys())[0]
    assert app.orders[order_key].order_total == pytest.approx(848.20, rel=1e-3)


def test_checkout_discount_code():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    app.load_discount_codes_from_dict(dummy_discount_codes)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("1775591963", 4)
    app.add_to_cart("4579334072", 1)
    app.checkout(discount_code="DISC10")

    assert app.orders is not None
    assert len(app.orders) == 1
    order_key = list(app.orders.keys())[0]
    assert app.orders[order_key].order_total == pytest.approx(606.465, rel=1e-3)


def test_checkout_discount_code_fail_one():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    app.load_discount_codes_from_dict(dummy_discount_codes)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("1775591963", 4)
    app.add_to_cart("4579334072", 1)
    with pytest.raises(ValueError):
        app.checkout(discount_code="DISC20")
    assert app.cart is not None
    assert len(app.cart) == 2
    assert app.cart["1775591963"].quantity == 4
    assert app.cart["4579334072"].quantity == 1


def test_checkout_discount_code_fail_two():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    app.load_discount_codes_from_dict(dummy_discount_codes)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("1775591963", 4)
    app.add_to_cart("4153505238", 1)
    with pytest.raises(ValueError):
        app.checkout(discount_code="DISC20")
    assert app.cart is not None
    assert len(app.cart) == 2
    assert app.cart["1775591963"].quantity == 4
    assert app.cart["4153505238"].quantity == 1


def test_checkout_empty_cart():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    with pytest.raises(Exception):
        app.checkout()
    assert not app.orders


def test_update_order_status():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    app.add_to_cart("4579334072", 1)
    app.checkout()
    order_key = list(app.orders.keys())[0]
    app.update_order_status(order_key, "shipped")
    assert app.orders[order_key].order_status == "shipped"


def test_cancel_order():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    app.add_to_cart("4579334072", 1)
    app.checkout()
    order_key = list(app.orders.keys())[0]
    app.cancel_order(order_key)
    assert app.orders[order_key].order_status == "cancelled"


def test_cancel_order_invalid_order():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    app.add_to_cart("4579334072", 1)
    app.checkout()
    with pytest.raises(ValueError):
        app.cancel_order("1234567890")


def test_cancel_order_delivered():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    app.add_to_cart("4579334072", 1)
    app.checkout()
    order_key = list(app.orders.keys())[0]
    app.update_order_status(order_key, "delivered")
    with pytest.raises(Exception):
        app.cancel_order(order_key)


def test_cancel_order_twice():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.add_to_cart("4153505238", 5)
    app.add_to_cart("4579334072", 1)
    app.checkout()
    order_key = list(app.orders.keys())[0]
    app.cancel_order(order_key)
    with pytest.raises(Exception):
        app.cancel_order(order_key)


def test_update_item():
    app = ShoppingApp()
    app.load_products_from_dict(dummy_data)
    environment = Environment()
    environment.register_apps([app])
    app.update_item(item_id="4153505238", new_price=100.0)
    assert app._get_item("4153505238")["price"] == 100.0
    app.update_item(item_id="4153505238", new_availability=False)
    assert app._get_item("4153505238")["available"] is False
