# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest

from are.simulation.apps.apartment_listing import ApartmentListingApp
from are.simulation.environment import Environment


@pytest.fixture(name="dummy_apartment_data")
def dummy_data():
    return {
        "apartment_1": {
            "apartment_id": "apartment_1",
            "name": "Sunny Apartment",
            "location": "Downtown",
            "price": 1200,
            "bedrooms": 2,
            "bathrooms": 1,
            "property_type": "Apartment",
            "square_footage": 850,
            "furnished_status": "Furnished",
            "floor_level": "Upper floors",
            "pet_policy": "Pets allowed",
            "lease_term": "1 year",
            "amenities": ["Gym", "Pool"],
            "zip_code": "10001",
        },
        "apartment_2": {
            "apartment_id": "apartment_2",
            "name": "Cozy Condo",
            "location": "Suburbs",
            "price": 900,
            "bedrooms": 1,
            "bathrooms": 1,
            "property_type": "Condo",
            "square_footage": 600,
            "furnished_status": "Unfurnished",
            "floor_level": "Ground floor",
            "pet_policy": "No pets",
            "lease_term": "6 months",
            "amenities": ["Parking", "Laundry"],
            "zip_code": "10002",
        },
        "apartment_3": {
            "apartment_id": "apartment_3",
            "name": "International Gardens",
            "location": "Midtown",
            "price": 2500,
            "bedrooms": 3,
            "bathrooms": 4,
            "property_type": "Home",
            "square_footage": 3000,
            "furnished_status": "Semi-furnished",
            "floor_level": "Third floor",
            "pet_policy": "No pets",
            "lease_term": "6 months",
            "amenities": ["Laundry"],
            "zip_code": "10003",
        },
    }


def test_load_apartments_from_dict(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    assert app.apartments is not None
    assert len(app.apartments) == 3


def test_list_all_apartments(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    apartments = app.list_all_apartments()
    assert apartments is not None
    assert len(apartments) == 3
    assert "apartment_1" in apartments
    assert "apartment_2" in apartments
    assert "apartment_3" in apartments


def test_get_apartment_details(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    apartment_details = app.get_apartment_details("apartment_1")
    assert apartment_details is not None
    assert apartment_details.name == "Sunny Apartment"
    assert apartment_details.location == "Downtown"
    with pytest.raises(ValueError):
        app.get_apartment_details("apartment_5")


def test_save_apartment(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    app.save_apartment("apartment_1")
    assert "apartment_1" in app.saved_apartments
    assert app.apartments["apartment_1"].saved
    with pytest.raises(ValueError):
        app.save_apartment("apartment_5")

    # Save the same apartment a second time and then remove it
    app.save_apartment("apartment_1")  # Attempt to save again
    app.remove_saved_apartment("apartment_1")  # Remove the apartment
    assert "apartment_1" not in app.saved_apartments
    assert not app.apartments["apartment_1"].saved


def test_remove_saved_apartment(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    app.save_apartment("apartment_1")
    app.remove_saved_apartment("apartment_1")
    assert "apartment_1" not in app.saved_apartments
    with pytest.raises(ValueError):
        app.remove_saved_apartment("apartment_2")


def test_list_saved_apartments(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    app.save_apartment("apartment_1")
    saved_apartments = app.list_saved_apartments()
    assert saved_apartments is not None
    assert len(saved_apartments) == 1
    assert "apartment_1" in saved_apartments


def test_search_apartments(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    results = app.search_apartments(
        location="Downtown", min_price=1000.0, max_price=1300.0
    )
    assert results is not None
    assert len(results) == 1
    assert "apartment_1" in results

    results = app.search_apartments(number_of_bedrooms=1, pet_policy="no Pets")
    assert results is not None
    assert len(results) == 1
    assert "apartment_2" in results

    results = app.search_apartments(name="Cozy Condo")
    assert results is not None
    assert len(results) == 1
    assert "apartment_2" in results

    results = app.search_apartments(min_price=900.0, pet_policy="no Pets")
    assert results is not None
    assert len(results) == 2
    assert "apartment_2" in results
    assert "apartment_3" in results

    results = app.search_apartments(
        min_price=900.0, pet_policy="no Pets", amenities=["laundry"]
    )
    assert results is not None
    assert len(results) == 2
    assert "apartment_2" in results
    assert "apartment_3" in results

    results = app.search_apartments(
        min_price=900.0, pet_policy="no Pets", amenities=["laundry", "salon"]
    )
    assert results is not None
    assert len(results) == 0

    results = app.search_apartments(min_price=2000.0, number_of_bathrooms=5)
    assert results is not None
    assert len(results) == 0

    results = app.search_apartments(location="Nonexistent")
    assert results is not None
    assert len(results) == 0


def test_search_saved_apartments(dummy_apartment_data):
    app = ApartmentListingApp()
    app.load_apartments_from_dict(dummy_apartment_data)
    environment = Environment()
    environment.register_apps([app])
    app.save_apartment("apartment_1")
    results = app.search_apartments(
        location="Downtown", min_price=1000.0, max_price=1300.0, saved_only=True
    )
    assert results is not None
    assert len(results) == 1
    assert "apartment_1" in results

    results = app.search_apartments(
        number_of_bedrooms=1, pet_policy="no Pets", saved_only=True
    )
    assert results is not None
    assert len(results) == 0
