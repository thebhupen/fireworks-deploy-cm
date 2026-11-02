# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest

from are.simulation.apps.city import CityApp
from are.simulation.environment import Environment

# Dummy crime data for testing
dummy_crime_data = {
    "10001": {"violent_crime": 15.2, "property_crime": 30.5},
    "90210": {"violent_crime": 5.3, "property_crime": 22.1},
    "30301": {"violent_crime": 20.8, "property_crime": 40.0},
}


def test_load_crime_data_from_dict():
    app = CityApp(api_call_limit=3)
    app.load_crime_data_from_dict(dummy_crime_data)
    environment = Environment()
    environment.register_apps([app])
    assert app.crime_data is not None
    assert len(app.crime_data) == 3


def test_get_crime_rate():
    app = CityApp(api_call_limit=3)
    app.load_crime_data_from_dict(dummy_crime_data)

    # Test valid zip code
    crime_rate = app.get_crime_rate("10001")
    assert crime_rate is not None
    assert crime_rate.violent_crime == 15.2
    assert crime_rate.property_crime == 30.5

    # Test invalid zip code
    with pytest.raises(ValueError):
        app.get_crime_rate("99999")

    # Test API call limit
    app.get_crime_rate("90210")
    with pytest.raises(Exception):
        app.get_crime_rate("10001")


def test_get_api_call_count():
    app = CityApp(api_call_limit=3)
    app.load_crime_data_from_dict(dummy_crime_data)

    # Check initial API call count
    assert app.get_api_call_count() == 0

    # Make API calls and verify the count
    app.get_crime_rate("10001")
    assert app.get_api_call_count() == 1

    with pytest.raises(ValueError):
        app.get_crime_rate("99999")
    assert app.get_api_call_count() == 2

    app.get_crime_rate("30301")
    assert app.get_api_call_count() == 3

    # Exceed the API call limit and check that the count remains at the limit
    with pytest.raises(Exception):
        app.get_crime_rate("90210")
    assert app.get_api_call_count() == 0  # API call count resets to 0
