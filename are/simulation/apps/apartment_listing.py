# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from are.simulation.apps.app import App
from are.simulation.tool_utils import app_tool, data_tool, env_tool
from are.simulation.types import EventType, OperationType, event_registered
from are.simulation.utils import get_state_dict, type_check, uuid_hex

logger = logging.getLogger(__name__)


@dataclass
class Apartment:
    name: str
    location: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: int
    property_type: str
    square_footage: int
    furnished_status: str | None = ""
    floor_level: str | None = ""
    pet_policy: str | None = ""
    lease_term: str | None = ""
    apartment_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    amenities: list[str] | None = field(default_factory=list)
    saved: bool = False

    def __post_init__(self):
        if self.apartment_id is None or len(self.apartment_id) == 0:
            self.apartment_id = uuid.uuid4().hex


@dataclass
class ApartmentListingApp(App):
    """
    A real estate application that manages and manipulates apartment listings. This class provides functionality
    for creating, reading, updating, and deleting apartment listings, as well as various utility methods for
    searching and filtering apartments based on multiple criteria.

    The app maintains apartments in a dictionary where each apartment is identified by a unique
    apartment_id. All price-related inputs should be in float format, and the number of bedrooms and bathrooms
    should be integers.

    Key Features:
        - Apartment Management: Add, update, delete, and retrieve apartment listings
        - Search Functionality: Filter apartments based on various criteria including location, price, size, and
          amenities
        - Favorites Management: Save and remove favorite apartments for quick access
        - State Management: Save and load application state to retain apartment listings and favorites

    Notes:
        - All apartment attributes are expected to adhere to specific data types (e.g., price as float, bedrooms
          and bathrooms as integers)
        - Apartment IDs are automatically generated when creating new apartments
        - The class supports state persistence through save/load operations from a file
        - Search operations are case-insensitive for string comparisons
        - Amenities filtering checks if all specified amenities are present in the apartment's amenities list
    """

    name: str | None = None
    # state of apartments - key is apartment ID and value is a dictionary of Apartment
    apartments: dict[str, Apartment] = field(default_factory=dict)
    # user saved apartments (favorites) - set of apartment IDs
    saved_apartments: list[str] = field(default_factory=list)

    def __post_init__(self):
        super().__init__(self.name)
        if len(self.saved_apartments) > 0:
            for apt_id in self.saved_apartments:
                self.apartments[apt_id].saved = True
        else:
            self.saved_apartments = [
                key for key in self.apartments if self.apartments[key].saved
            ]

    def get_state(self) -> dict[str, Any] | None:
        return get_state_dict(self, ["apartments", "saved_apartments"])

    def load_state(self, state_dict: dict[str, Any]):
        self.load_apartments_from_dict(state_dict["apartments"])
        self.saved_apartments = state_dict["saved_apartments"]
        for apt_id in self.saved_apartments:
            self.apartments[apt_id].saved = True

    def reset(self):
        super().reset()
        self.apartments = {}
        self.saved_apartments = []

    def load_apartments_from_file(self, path: str):
        try:
            with open(path) as f:
                apts_dict = json.load(f)
                self.load_apartments_from_dict(apts_dict)
        except Exception as e:
            logger.exception(e)

    def load_apartments_from_dict(self, apartments: dict[str, dict[str, Any]]):
        for apt in apartments:
            apartments[apt]["apartment_id"] = apt
            self.apartments[apt] = Apartment(**apartments[apt])

    def _get_apartment(self, apartment_id: str) -> Apartment | None:
        """
        given an apartment_id, return the apartment details
        """
        return self.apartments.get(apartment_id)

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_new_apartment(
        self,
        name: str,
        location: str,
        zip_code: str,
        price: float,
        number_of_bedrooms: int,
        number_of_bathrooms: int,
        square_footage: int,
        property_type: str = "",
        furnished_status: str = "",
        floor_level: str = "",
        pet_policy: str = "",
        lease_term: str = "",
        amenities: list[str] | None = None,
    ) -> str:
        """
        Adds a new apartment to the apartment listing.
        :param name: name of the apartment
        :param location: desired location
        :param zip_code: zip code of the apartment location
        :param price: price of the apartment
        :param number_of_bedrooms: number of bedrooms
        :param number_of_bathrooms: number of bathrooms
        :param property_type: type of property (Apartment, Condo, etc.)
        :param square_footage: minimum square footage
        :param furnished_status: Furnished, Unfurnished, or Semi-furnished
        :param floor_level: Ground floor, Upper floors, Penthouse, Basement
        :param pet_policy: Pets allowed, No pets, Cats allowed, Dogs allowed
        :param lease_term: Month-to-month, 6 months, 1 year, Long term lease
        :param amenities: list of desired amenities
        :returns: apartment_id of the apartment just added, if successful, otherwise raise Exception.
        """
        if amenities is None:
            amenities = []
        apartment_id = uuid_hex(self.rng)
        self.apartments[apartment_id] = Apartment(
            name=name,
            location=location,
            zip_code=zip_code,
            price=price,
            bedrooms=number_of_bedrooms,
            bathrooms=number_of_bathrooms,
            property_type=property_type,
            square_footage=square_footage,
            furnished_status=furnished_status,
            floor_level=floor_level,
            pet_policy=pet_policy,
            lease_term=lease_term,
            amenities=amenities,
            apartment_id=apartment_id,
        )
        return apartment_id

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_apartment(
        self,
        apartment_id: str,
        new_price: float,
    ) -> str:
        """
        Updates an existing apartment in the apartment listing.
        :param apartment_id: apartment id to update
        :param new_price: new price of the apartment
        :returns: apartment_id of the apartment just updated, if successful, otherwise raise Exception.
        """
        if apartment_id not in self.apartments:
            raise ValueError("Apartment does not exist")
        self.apartments[apartment_id].price = new_price
        return apartment_id

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def delete_apartment(self, apartment_id: str) -> None:
        """
        Deletes a specific apartment by apartment_id.
        :param apartment_id: apartment id to delete
        :returns: apartment_id of the apartment just deleted, if successful, otherwise raise Exception.
        """
        if apartment_id in self.apartments:
            del self.apartments[apartment_id]
        else:
            raise ValueError("Apartment does not exist.")

    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_all_apartments(self) -> dict[str, Any]:
        """
        List all apartments in the catalog.
        :returns: apartment details
        """
        return self.apartments

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_apartment_details(self, apartment_id: str) -> Apartment:
        """
        Get apartment details for a given apartment id.
        :param apartment_id: apartment id to get details for
        :returns: apartment details
        """
        if apartment_id not in self.apartments:
            raise ValueError("Apartment does not exist")
        return self.apartments[apartment_id]

    @type_check
    @app_tool(llm_formatter=lambda x: "Successfully saved apartment")
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def save_apartment(self, apartment_id: str) -> None:
        """
        Save an apartment to favorites if not already saved, otherwise do nothing.
        :param apartment_id: apartment id to save
        """
        if apartment_id not in self.apartments:
            raise ValueError("Apartment does not exist")
        if apartment_id not in self.saved_apartments:
            self.saved_apartments.append(apartment_id)
            self.apartments[apartment_id].saved = True

    @type_check
    @app_tool(llm_formatter=lambda x: "Successfully removed apartment from favorites")
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_saved_apartment(self, apartment_id: str) -> None:
        """
        Remove an apartment from favorites.
        :param apartment_id: apartment id to remove
        """
        if apartment_id not in self.saved_apartments:
            raise ValueError("Apartment not in saved list")
        self.saved_apartments.remove(apartment_id)
        self.apartments[apartment_id].saved = False

    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_saved_apartments(self) -> dict[str, Apartment]:
        """
        List apartments saved to favorites.
        :returns: Dictionary of saved apartments: apartment_id -> apartment
        """
        return {apt_id: self.apartments[apt_id] for apt_id in self.saved_apartments}

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_apartments(
        self,
        name: str | None = None,
        location: str | None = None,
        zip_code: str | None = None,
        min_price: int | float | None = None,
        max_price: int | float | None = None,
        number_of_bedrooms: int | None = None,
        number_of_bathrooms: int | None = None,
        property_type: str | None = None,
        square_footage: int | None = None,
        furnished_status: str | None = None,
        floor_level: str | None = None,
        pet_policy: str | None = None,
        lease_term: str | None = None,
        amenities: list[str] | None = None,
        saved_only: bool = False,
    ) -> dict[str, Apartment]:
        """
        Search for apartments based on multiple filters.
        :param name: name of the apartment
        :param location: desired location
        :param zip_code: zip code of the location
        :param min_price: minimum price
        :param max_price: maximum price
        :param number_of_bedrooms: number of bedrooms
        :param number_of_bathrooms: number of bathrooms
        :param property_type: type of property (Apartment, Condo, etc.)
        :param square_footage: minimum square footage
        :param furnished_status: Furnished, Unfurnished, or Semi-furnished
        :param floor_level: Ground floor, Upper floors, Penthouse, Basement
        :param pet_policy: Pets allowed, No pets, Cats allowed, Dogs allowed
        :param lease_term: Month-to-month, 6 months, 1 year, Long term lease
        :param amenities: list of desired amenities
        :param saved_only: if True, search only saved apartments; if False, search all apartments (default)
        :returns: filtered list of apartments, dictionary of apartment_id -> apartment
        """
        # Determine apartment set to search
        if saved_only:
            apartments_to_search = {
                apt_id: self.apartments[apt_id] for apt_id in self.saved_apartments
            }
        else:
            apartments_to_search = self.apartments

        # Prepare case-insensitive search terms
        name_lower = name.lower() if name else None
        location_lower = location.lower() if location else None
        property_type_lower = property_type.lower() if property_type else None
        furnished_status_lower = furnished_status.lower() if furnished_status else None
        pet_policy_lower = pet_policy.lower() if pet_policy else None
        lease_term_lower = lease_term.lower() if lease_term else None
        amenities_lower = [am.lower() for am in amenities] if amenities else None

        # Apply filters
        filtered_apartments = {}

        for apt_id, apt in apartments_to_search.items():
            # Fast numeric filters first
            if min_price and apt.price < min_price:
                continue
            if max_price and apt.price > max_price:
                continue
            if number_of_bedrooms and apt.bedrooms != number_of_bedrooms:
                continue
            if number_of_bathrooms and apt.bathrooms != number_of_bathrooms:
                continue
            if square_footage and apt.square_footage < square_footage:
                continue

            # Exact match filters
            if zip_code and apt.zip_code != zip_code:
                continue
            if floor_level and apt.floor_level != floor_level:
                continue

            # String filters
            if name_lower and name_lower not in apt.name.lower():
                continue
            if location_lower and location_lower not in apt.location.lower():
                continue
            if property_type_lower and apt.property_type.lower() != property_type_lower:
                continue
            if (
                furnished_status_lower
                and apt.furnished_status
                and apt.furnished_status.lower() != furnished_status_lower
            ):
                continue
            if (
                pet_policy_lower
                and apt.pet_policy
                and apt.pet_policy.lower() != pet_policy_lower
            ):
                continue
            if (
                lease_term_lower
                and apt.lease_term
                and apt.lease_term.lower() != lease_term_lower
            ):
                continue

            # Amenities filter
            if amenities_lower:
                apt_amenities_lower = [t.lower() for t in (apt.amenities or [])]
                if not all(am in apt_amenities_lower for am in amenities_lower):
                    continue

            filtered_apartments[apt_id] = apt

        return filtered_apartments


@dataclass
class RentAFlat(ApartmentListingApp):
    __doc__ = ApartmentListingApp.__doc__
    name: str | None = "RentAFlat"
