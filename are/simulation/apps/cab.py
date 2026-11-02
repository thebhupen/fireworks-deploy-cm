# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from are.simulation.apps.app import App
from are.simulation.tool_utils import OperationType, app_tool, data_tool, env_tool
from are.simulation.types import EventType, disable_events, event_registered
from are.simulation.utils import get_state_dict, type_check, uuid_hex

DEFAULT_RIDE_CANCELLED_MESSAGE = (
    "The ride has been cancelled. Sorry for the inconvenience."
)


@dataclass
class Ride:
    ride_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str | None = None
    service_type: str | None = None
    start_location: str | None = None
    end_location: str | None = None
    price: float | None = None
    duration: float | None = None
    time_stamp: float | None = None
    distance_km: float | None = None
    delay: float | None = None
    delay_history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if self.ride_id is None or len(self.ride_id) == 0:
            self.ride_id = uuid.uuid4().hex

    def set_booked(self):
        self.status = "BOOKED"
        self.delay_history.append({"delay": self.delay, "time_stamp": self.time_stamp})

    def update_delay(self, current_time_stamp: float, rng: random.Random):
        if self.time_stamp is None or self.delay is None:
            raise ValueError("time_stamp or delay is not set")
        delta_time = current_time_stamp - self.time_stamp
        self.delay = min(0, self.delay - delta_time * (1 + rng.uniform(-1.5, 1)))
        self.delay_history.append({"delay": self.delay, "time_stamp": self.time_stamp})

    def __str__(self):
        return f"""
        Ride ID: {self.ride_id}
        Status: {self.status}
        Service Type: {self.service_type}
        Start Location: {self.start_location}
        End Location: {self.end_location}
        Distance: {self.distance_km} kms
        Price: ${self.price:.2f}
        Duration: {"N/A" if self.duration is None else self.duration / 60} mins
        Timestamp: {self.time_stamp}
        Delay: {"N/A" if self.delay is None else self.delay / 60} mins
        """


@dataclass
class RideHistory:
    name: str
    rides: list[Ride]


@dataclass
class OnGoingRide:
    name: str
    ride: Ride | None = None


@dataclass
class CabApp(App):
    """
    A cab service application that manages and facilitates ride requests and bookings. This class provides
    functionality for creating, reading, updating, and canceling rides, as well as calculating fares and
    handling ride history.

    The CabApp maintains rides in a structured format, allowing users to book rides, view current ride status,
    and retrieve ride history. Each ride is represented by a unique Ride object, containing relevant details
    about the journey.

    Key Features:
        - Ride Management: Create, book, cancel, and retrieve ride details
        - Quotation System: Calculate fare estimates based on distance, service type, and historical data
        - Ride History: Track past rides and access details for each ride
        - Delay Management: Update and record delays for ongoing rides
        - State Persistence: Save and load application state to retain ride and quotation history

    Notes:
        - All ride attributes are expected to conform to specific data types (e.g., price as float, distance
          as float)
        - Ride IDs are automatically generated upon creation
        - The class allows for the cancellation of rides by both users and drivers
        - Fare calculations consider historical pricing trends and maximum service distances
        - The distance calculation is currently a mock function; integration with a real mapping API is
          recommended for accurate distance measurements
    """

    name: str | None = None
    quotation_history: list[Ride] = field(default_factory=list)
    on_going_ride: Ride | None = None
    ride_history: list[Ride] = field(default_factory=list)
    MESSAGE_CANCEL: str = DEFAULT_RIDE_CANCELLED_MESSAGE
    d_service_config: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "Default": {
                "nb_seats": 4,
                "price_per_km": 1.0,
                "base_delay_min": 5,
                "max_distance_km": 25,
            },
            "Premium": {
                "nb_seats": 4,
                "price_per_km": 2.0,
                "base_delay_min": 3,
                "max_distance_km": 25,
            },
            "Van": {
                "nb_seats": 6,
                "price_per_km": 1.5,
                "base_delay_min": 7,
                "max_distance_km": 25,
            },
        }
    )

    def __post_init__(self):
        super().__init__(self.name)

    def get_state(self) -> dict[str, Any]:
        return get_state_dict(
            self,
            [
                "ride_history",
                "quotation_history",
                "d_service_config",
            ],
        )

    def load_state(self, state_dict: dict[str, Any]):
        for ride_history in state_dict["ride_history"]:
            if "cab_app" in ride_history:
                ride_history.pop("cab_app")
            if "seed" in ride_history:
                ride_history.pop("seed")
            self.ride_history.append(Ride(**ride_history))
        for ride_history in state_dict["quotation_history"]:
            if "cab_app" in ride_history:
                ride_history.pop("cab_app")
            if "seed" in ride_history:
                ride_history.pop("seed")
            self.quotation_history.append(Ride(**ride_history))
        self.d_service_config = state_dict["d_service_config"]

    def reset(self):
        super().reset()
        self.ride_history = []
        self.quotation_history = []
        self.d_service_config = {}
        self.on_going_ride = None

    def _parse_ride_time(self, ride_time: str | None = None) -> tuple[str, float]:
        """
        Parse and validate ride time, providing default if None.

        :param ride_time: Optional ride time string in 'YYYY-MM-DD HH:MM:SS' format
        :returns: Tuple of (formatted_time_string, timestamp_float)
        :raises ValueError: If ride_time format is invalid
        """
        # Generate default time if not provided
        if ride_time is None:
            ride_time = datetime.fromtimestamp(
                self.time_manager.time(), tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S")

        # Parse and validate the time string
        try:
            time_stamp = (
                datetime.strptime(ride_time, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        except ValueError:
            raise ValueError(
                "Invalid datetime format for the ride time. Please use YYYY-MM-DD HH:MM:SS"
            )

        return ride_time, time_stamp

    def calculate_price(
        self,
        start_location: str,
        end_location: str,
        distance_km: float,
        service_type: str,
        time_stamp,
    ) -> float:
        def get_previous_price():
            for ride in self.quotation_history:
                if (
                    ride.start_location == start_location
                    and ride.end_location == end_location
                    and ride.service_type == service_type
                ):
                    return ride
            return None

        ex = get_previous_price()
        if ex and ex.price:
            variance = 0.01 * (time_stamp - ex.time_stamp) / 3600  # 1% per hour
            variance = min(max(variance, 0.5), 1.5)  # bounded
            price = ex.price * (1 + self.rng.uniform(-variance, variance))
        else:
            price = distance_km * self.d_service_config[service_type]["price_per_km"]
        return price

    @type_check
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_new_ride(
        self,
        service_type: str,
        start_location: str,
        end_location: str,
        price: float,
        duration: float = 0.0,
        time_stamp: float = 0.0,
        distance_km: float = 0.0,
    ) -> str:
        """
        Add a new ride to the ride history.
        :param service_type: type of service (Default, Premium, Van)
        :param start_location: starting point of the ride
        :param end_location: ending point of the ride
        :param price: price of the ride
        :param duration: duration in minutes of the ride
        :param time_stamp: time stamp of the ride
        :param distance_km: distance in kilometers of the ride
        :return: ride id of the added ride if successful, otherwise raise Exception.
        """
        status = "BOOKED"
        ride = Ride(
            ride_id=uuid_hex(self.rng),
            status=status,
            service_type=service_type,
            start_location=start_location,
            end_location=end_location,
            price=price,
            duration=duration,
            time_stamp=time_stamp,
            distance_km=distance_km,
        )
        self.ride_history.append(ride)
        self.quotation_history.append(ride)
        return ride.ride_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_quotation(
        self,
        start_location: str,
        end_location: str,
        service_type: str,
        ride_time: str | None = None,
    ) -> Ride:
        """
        Calculates the price and estimated delay for a ride.
        :param start_location: starting point of the ride
        :param end_location: ending point of the ride
        :param service_type: type of service (Default, Premium, Van)
        :param ride_time: the time of the ride in the format 'YYYY-MM-DD HH:MM:SS'. If None, the current time is used.
        :returns: Ride with all the information: start_location, end_location, service_type, price, delay, distance, duration, the time_stamp.
        """
        _, time_stamp = self._parse_ride_time(ride_time)

        if service_type not in self.d_service_config:
            raise ValueError("Invalid service type.")

        distance_km = self.calculate_distance(start_location, end_location)
        if distance_km > self.d_service_config[service_type]["max_distance_km"]:
            raise ValueError("Distance exceeds maximum allowed.")

        price = self.calculate_price(
            start_location, end_location, distance_km, service_type, time_stamp
        )
        delay = self.d_service_config[service_type][
            "base_delay_min"
        ] + self.rng.randint(1, 5)
        duration = (
            distance_km / 50 * 60 + 10 * self.rng.random()
        )  # Assuming average speed of 50 km/h

        ride = Ride(
            ride_id=uuid_hex(self.rng),
            service_type=service_type,
            start_location=start_location,
            end_location=end_location,
            price=price,
            duration=duration,
            time_stamp=time_stamp,
            distance_km=distance_km,
            delay=delay,
        )
        self.quotation_history.append(ride)
        return ride

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_rides(
        self,
        start_location: str,
        end_location: str,
        ride_time: str | None = None,
    ) -> list[Ride]:
        """
        Lists all rides available between two locations.
        :param start_location: starting point of the ride
        :param end_location: ending point of the ride
        :param ride_time: the time of the ride. If None, the current time is used.
        :returns: list of Ride objects
        """
        ride_time_str, _ = self._parse_ride_time(ride_time)

        all_rides = []
        for service_type in self.d_service_config.keys():
            ride = self.get_quotation(
                start_location,
                end_location,
                service_type,
                ride_time=ride_time_str,
            )
            all_rides.append(ride)
        return all_rides

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def order_ride(
        self,
        start_location: str,
        end_location: str,
        service_type: str,
        ride_time: str | None = None,
    ) -> Ride:
        """
        Orders a ride and returns the ride details.
        :param start_location: starting point of the ride
        :param end_location: ending point of the ride
        :param service_type: type of service (Default, Premium, Van)
        :param ride_time: the time of the ride
        :returns: booked ride, represented by a Ride object
        """
        if self.on_going_ride is not None:
            raise ValueError("You have an on-going ride.")

        ride_time_str, _ = self._parse_ride_time(ride_time)

        # Note that here the app looks for a cab but the user is not aware of the delay.
        ride = self.get_quotation(
            start_location, end_location, service_type, ride_time_str
        )
        ride.set_booked()
        self.ride_history.append(ride)
        self.on_going_ride = ride
        return ride

    @data_tool()
    @env_tool()
    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def cancel_ride(
        self, who_cancel: str = "driver", message: str | None = None
    ) -> str:
        """
        The current ride is cancelled (by user or by driver).
        :param who_cancel: who cancel the ride, either 'driver' or 'user'
        :param message: optional message to send to the user
        :returns: message
        """
        if who_cancel not in ["driver", "user"]:
            raise ValueError("who_cancel must be either 'driver' or 'user'.")
        if self.on_going_ride is None:
            raise ValueError("You have no on-going ride.")
        assert self.on_going_ride == self.ride_history[-1]
        self.on_going_ride.status = "CANCELLED"
        self.on_going_ride = None

        message = message if message else self.MESSAGE_CANCEL
        return message

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def user_cancel_ride(self):
        """
        Cancel the current ride.
        """
        message = "Ride has been cancelled, sorry to see you go."
        with disable_events():
            message = self.cancel_ride(who_cancel="user", message=message)
        return message

    @env_tool()
    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def end_ride(self) -> str:
        """
        End the current ride.
        :returns: "Ride has been completed."
        """
        if self.on_going_ride is None:
            raise ValueError("You have no on-going ride.")
        assert self.on_going_ride == self.ride_history[-1]
        self.on_going_ride.status = "COMPLETED"
        self.on_going_ride = None
        return "Ride has been completed."

    @env_tool()
    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_ride_status(self, status: str, message: str | None = None):
        """
        Update the status of the current ride.
        :param status: new status of the ride. Must be one of "DELAYED", "IN_PROGRESS", "ARRIVED_AT_PICKUP".
        :param message: optional message from the driver.
        :returns: new status of the ride
        """
        if status not in ["DELAYED", "IN_PROGRESS", "ARRIVED_AT_PICKUP"]:
            raise ValueError(
                "status must be one of 'DELAYED', 'IN_PROGRESS', 'ARRIVED_AT_PICKUP'"
            )
        if self.on_going_ride is None:
            raise ValueError("You have no on-going ride.")
        assert self.on_going_ride == self.ride_history[-1]
        self.on_going_ride.status = status
        if message:
            out_message = f"Ride status has been updated to {status}. Message from your driver: {message}"
        else:
            out_message = f"Ride status has been updated to {status}."
        return out_message

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_current_ride_status(self) -> Ride:
        """
        Check the status for the current ride ordered.
        :returns: ride details, represented by a Ride object
        """
        if self.on_going_ride:
            self.on_going_ride.update_delay(self.time_manager.time(), self.rng)
            return self.on_going_ride
        else:
            raise ValueError("No ride ordered.")

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_ride(self, idx: int):
        """
        Gets a specific ride from the ride history.
        :param idx: index of the ride to retrieve
        :returns: ride details
        """
        if 0 <= idx < len(self.ride_history):
            return self.ride_history[idx]
        else:
            raise IndexError("Ride does not exist.")

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_ride_history(self, offset: int = 0, limit: int = 10) -> dict[str, Any]:
        """
        Gets a list of rides from the ride history starting from a specified offset.
        :param offset: starting point to retrieve rides from, default is 0.
        :param limit: maximum number of rides to retrieve, default is 10.
        :returns: dictionary of ride details, where the key is the index of the ride in the ride history and the value is the ride details, with additional metadata about the range of rides retrieved and total number of rides.
        """
        ride_history_subset = self.ride_history[offset : offset + limit]
        return {
            "rides": {
                offset + idx: ride for idx, ride in enumerate(ride_history_subset)
            },
            "range": (
                offset,
                min(offset + limit, len(self.ride_history)),
            ),
            "total": len(self.ride_history),
        }

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_ride_history_length(self) -> int:
        """
        Gets the length of the ride history.
        :returns: length of the ride history
        """
        return len(self.ride_history)

    def get_distance_from_history(self, start_location, end_location):
        for ride in self.quotation_history:
            if (
                ride.start_location == start_location
                and ride.end_location == end_location
            ):
                return ride.distance_km
        return None

    def calculate_distance(self, start_location: str, end_location: str) -> float:
        """
        Mock function to calculate the distance between two locations.
        :param start_location: starting point of the ride
        :param end_location: ending point of the ride
        :returns: distance in kilometers
        """
        distance = self.get_distance_from_history(start_location, end_location)
        if not distance:
            # In a real-world scenario, you would integrate with a mapping service API to calculate the distance
            distance = self.rng.uniform(5, 20)  # Mock distance between 5 and 20 km
        return distance

    def delete_future_data(self, timestamp):
        """
        Delete all future data from the ride history.
        :param timestamp: timestamp to delete data after
        """
        self.ride_history = [
            ride for ride in self.ride_history if ride.time_stamp <= timestamp
        ]
        self.quotation_history = [
            ride for ride in self.quotation_history if ride.time_stamp <= timestamp
        ]
