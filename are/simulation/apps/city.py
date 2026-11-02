# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from dataclasses import dataclass, field
from typing import Any

from are.simulation.apps.app import App
from are.simulation.tool_utils import OperationType, app_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import get_state_dict, type_check


@dataclass
class CrimeDataPoint:
    violent_crime: float
    property_crime: float


logger = logging.getLogger(__name__)


@dataclass
class CityApp(App):
    """
    A city information application that provides access to crime rate data for different zip codes.
    This class implements a rate-limited API service for retrieving crime statistics, with built-in
    tracking of API usage and enforcement of call limits.

    The CityApp maintains crime data in a dictionary where each zip code is mapped to its corresponding
    crime statistics. The free version of the API has usage limitations that are strictly enforced.

    Key Features:
        - Crime Data Access: Retrieve crime statistics for specific zip codes
        - Rate Limiting: Implements usage restrictions with 30-minute cooldown
        - API Usage Tracking: Monitors and manages API call counts
        - State Management: Save and load application state
        - Data Loading: Support for loading crime data from files or dictionaries

    Notes:
        - Free version is limited to 100 API calls per 30-minute period
        - Rate limit reset requires a 30-minute waiting period
        - API calls are tracked and persist until manually reset
        - Attempting to exceed rate limits raises an exception
        - Invalid zip codes result in ValueError
    """

    name: str | None = None
    api_call_count: int = 0
    api_call_limit: int = 100
    rate_limit_cooldown_seconds = 1800  # 30 minutes
    crime_data: dict[str, CrimeDataPoint] = field(default_factory=dict)
    rate_limit_time: float | None = None
    rate_limit_exceeded: bool = False

    def __post_init__(self):
        super().__init__(self.name)

    def get_state(self) -> dict[str, Any] | None:
        return get_state_dict(self, ["api_call_limit", "crime_data"])

    def load_state(self, state_dict: dict[str, Any]):
        self.load_crime_data_from_dict(state_dict["crime_data"])
        self.api_call_limit = state_dict["api_call_limit"]

    def reset(self):
        super().reset()
        self.crime_data = {}
        self.api_call_count = 0

    def load_crime_data_from_dict(self, crime_data):
        self.crime_data = {}
        for zipcode in crime_data:
            self.crime_data[zipcode] = CrimeDataPoint(**crime_data[zipcode])

    def _is_rate_limited(self) -> bool:
        """Check if API calls are currently rate limited."""
        # First time hitting the limit
        if self.api_call_count >= self.api_call_limit and self.rate_limit_time is None:
            return True

        # Still in cooldown period
        if self.rate_limit_time is not None:
            time_since_limit = self.time_manager.time() - self.rate_limit_time
            return time_since_limit < self.rate_limit_cooldown_seconds

        return False

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by setting state and raising exception."""
        if self.rate_limit_time is None:
            self.rate_limit_time = self.time_manager.time()

        self.reset_api_call_count()
        self.rate_limit_exceeded = True

        raise ValueError(
            f"Free version only supports {self.api_call_limit} API calls. "
            f"Please try again after 30 minutes or upgrade to pro-version."
        )

    def _reset_rate_limit_if_expired(self) -> None:
        """Reset rate limit if cooldown period has passed."""
        if (
            self.rate_limit_time is not None
            and self.time_manager.time() - self.rate_limit_time
            >= self.rate_limit_cooldown_seconds
        ):
            self.rate_limit_time = None
            self.rate_limit_exceeded = False

    @env_tool()
    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_crime_rate(
        self, zip_code: str, violent_crime_rate: float, property_crime_rate: float
    ) -> str:
        """
        Add crime rate for a given zip code.
        :param zip_code: zip code to add crime rate for
        :param violent_crime_rate: violent crime rate
        :param property_crime_rate: property crime rate
        :return: Success message
        """
        self.crime_data[zip_code] = CrimeDataPoint(
            violent_crime=violent_crime_rate,
            property_crime=property_crime_rate,
        )
        return "Added Successfully"

    @env_tool()
    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_crime_rate(
        self,
        zip_code: str,
        new_violent_crime_rate: float | None = None,
        new_property_crime_rate: float | None = None,
    ) -> str:
        """
        Update crime rate for a given zip code.
        :param zip_code: zip code to update crime rate for
        :param new_violent_crime_rate: violent crime rate
        :param new_property_crime_rate: property crime rate
        :return: Success message
        """
        if new_violent_crime_rate is None and new_property_crime_rate is None:
            raise ValueError("No update provided")
        if zip_code not in self.crime_data:
            raise ValueError("Zip code does not exist in our database")
        crime_datapoint = self.crime_data[zip_code]
        if new_violent_crime_rate is not None:
            crime_datapoint.violent_crime = new_violent_crime_rate
        if new_property_crime_rate is not None:
            crime_datapoint.property_crime = new_property_crime_rate
        return "Updated Successfully"

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_crime_rate(self, zip_code: str) -> CrimeDataPoint:
        """
        Get crime rate for a given zip code. This is a free version of the API, so it has a limit.
        This limit can be obtained by calling get_api_call_limit() method.
        If you exceed this limit, you have to wait for 30 minutes to make more calls.
        :param zip_code: zip code to get crime rate for
        :returns: crime rate details
        """

        # Reset rate limit if cooldown expired
        self._reset_rate_limit_if_expired()

        # Check and enforce rate limiting
        if self._is_rate_limited():
            self._enforce_rate_limit()

        self.api_call_count += 1

        if zip_code not in self.crime_data:
            raise ValueError("Zip code does not exist in our database")

        return self.crime_data[zip_code]

    def reset_api_call_count(self) -> None:
        """
        Reset the API call count
        :returns: None
        """
        self.api_call_count = 0

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_api_call_count(self) -> int:
        """
        Get the current API call count for the service.
        :returns: API call count
        """
        return self.api_call_count

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_api_call_limit(self) -> int:
        """
        Get the API call limit rate for the service.
        :returns: API call count
        """
        return self.api_call_limit
