# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.apps.cab import CabApp


def test_deterministic_price():
    cab_app_x = CabApp()
    start_location = "A"
    end_location = "B"
    service_type = "Default"
    ride_time = "2022-01-01 12:00:00"
    price1_x = cab_app_x.get_quotation(
        start_location, end_location, service_type, ride_time
    ).price
    price2_x = cab_app_x.get_quotation(
        start_location, end_location, service_type, ride_time
    ).price
    cab_app_y = CabApp()
    price1_y = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).price
    price2_y = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).price

    d_service_config = cab_app_y.d_service_config.copy()
    cab_app_y.reset()
    cab_app_y.d_service_config = d_service_config
    price1_z = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).price
    price2_z = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).price
    assert price1_x == price1_y, f"price1_x: {price1_x}, price1_y: {price1_y}"
    assert price2_x == price2_y, f"price2_x: {price2_x}, price2_y: {price2_y}"
    assert price1_z == price1_y, f"price1_z: {price1_z}, price1_y: {price1_y}"
    assert price2_z == price2_y, f"price2_z: {price2_z}, price2_y: {price2_y}"


def test_deterministic_distance():
    cab_app_x = CabApp()
    start_location = "A"
    end_location = "B"
    distance1_x = cab_app_x.calculate_distance(start_location, end_location)
    distance2_x = cab_app_x.calculate_distance(start_location, end_location)
    cab_app_y = CabApp()
    distance1_y = cab_app_y.calculate_distance(start_location, end_location)
    distance2_y = cab_app_y.calculate_distance(start_location, end_location)
    assert distance1_x == distance1_y, (
        f"distance1_x: {distance1_x}, distance1_y: {distance1_y}"
    )
    assert distance2_x == distance2_y, (
        f"distance2_x: {distance2_x}, distance2_y: {distance2_y}"
    )


def test_deterministic_delay():
    cab_app_x = CabApp()
    start_location = "A"
    end_location = "B"
    service_type = "Default"
    ride_time = "2022-01-01 12:00:00"
    delay1_x = cab_app_x.get_quotation(
        start_location, end_location, service_type, ride_time
    ).delay
    delay2_x = cab_app_x.get_quotation(
        start_location, end_location, service_type, ride_time
    ).delay
    cab_app_y = CabApp()
    delay1_y = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).delay
    delay2_y = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).delay
    assert delay1_x == delay1_y, f"delay1_x: {delay1_x}, delay1_y: {delay1_y}"
    assert delay2_x == delay2_y, f"delay2_x: {delay2_x}, delay2_y: {delay2_y}"


def test_deterministic_duration():
    cab_app_x = CabApp()
    start_location = "A"
    end_location = "B"
    service_type = "Default"
    ride_time = "2022-01-01 12:00:00"
    duration1_x = cab_app_x.get_quotation(
        start_location, end_location, service_type, ride_time
    ).duration
    duration2_x = cab_app_x.get_quotation(
        start_location, end_location, service_type, ride_time
    ).duration
    cab_app_y = CabApp()
    duration1_y = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).duration
    duration2_y = cab_app_y.get_quotation(
        start_location, end_location, service_type, ride_time
    ).duration
    assert duration1_x == duration1_y, (
        f"duration1_x: {duration1_x}, duration1_y: {duration1_y}"
    )
    assert duration2_x == duration2_y, (
        f"duration2_x: {duration2_x}, duration2_y: {duration2_y}"
    )
