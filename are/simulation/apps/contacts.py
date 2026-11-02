# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import copy
import textwrap
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from are.simulation.apps.app import App
from are.simulation.tool_utils import OperationType, app_tool, data_tool
from are.simulation.types import event_registered
from are.simulation.utils import get_state_dict, type_check, uuid_hex


class Gender(Enum):
    FEMALE = "Female"
    MALE = "Male"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class Status(Enum):
    STUDENT = "Student"
    EMPLOYED = "Employed"
    UNEMPLOYED = "Unemployed"
    RETIRED = "Retired"
    UNKNOWN = "Unknown"


@dataclass
class Contact:
    first_name: str
    last_name: str
    contact_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    is_user: bool = False
    gender: Gender = Gender.UNKNOWN
    age: int | None = None
    nationality: str | None = None
    city_living: str | None = None
    country: str | None = None
    status: Status = Status.UNKNOWN
    job: str | None = None
    description: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None

    def _validate_enum_field(self, value, enum_class):
        """Ultra-simple enum validation with case-insensitive support."""
        if isinstance(value, enum_class):
            return value

        if isinstance(value, str):
            # Handle "Gender.FEMALE" -> "FEMALE"
            if "." in value:
                value = value.split(".")[-1]

            # Try different case variations
            for enum_member in enum_class:
                if (
                    value.lower() == enum_member.name.lower()
                    or value.lower() == enum_member.value.lower()
                ):
                    return enum_member

        return enum_class(value)  # Let enum raise its own ValueError

    def __post_init__(self):
        if self.first_name is None:
            raise ValueError("Invalid first name.")

        if self.last_name is None:
            raise ValueError("Invalid last name.")

        if self.contact_id is None or len(self.contact_id) == 0:
            self.contact_id = uuid.uuid4().hex

        # Gender check
        self.gender = self._validate_enum_field(self.gender, Gender)

        # Age check
        if self.age is not None and not 1 <= self.age <= 100:
            raise ValueError("Invalid age.", self.age)

        # Status check
        self.status = self._validate_enum_field(self.status, Status)

    def __str__(self):
        return textwrap.dedent(
            f"""
        Contact ID: {self.contact_id}
        First Name: {self.first_name}
        Last Name: {self.last_name}
        Gender: {self.gender}
        Age: {self.age}
        Nationality: {self.nationality}
        City Living: {self.city_living}
        Country: {self.country}
        Status: {self.status}
        Job: {self.job}
        Description: {self.description}
        Phone: {self.phone}
        Email: {self.email}
        Is User: {self.is_user}
        Address: {self.address}
        """
        )

    @property
    def summary(self):
        return f"id:{self.contact_id}\n{self.first_name} {self.last_name}: 📞 {self.phone} 📧 {self.email}"


@dataclass
class ContactsApp(App):
    """
    A contacts management application that handles storage, retrieval, and manipulation of contact information.
    This class provides comprehensive functionality for managing a contact database with pagination support
    and search capabilities.

    The ContactsApp stores contacts in a dictionary where each contact is identified by a unique contact_id.
    The application implements a view limit mechanism for paginated access to contacts.

    Key Features:
        - Contact Management: Add, edit, delete, and retrieve contact information
        - Pagination: View contacts with offset and limit support
        - Search Functionality: Search contacts by name, phone, or email
        - Current User: Special handling for current user's contact information
        - State Management: Save and load application state
        - Batch Operations: Support for adding multiple contacts at once

    Notes:
        - Contact fields include: first/last name, gender, age, nationality, city, status, job, address etc.
        - Gender options: Male, Female, Other, Unknown (default)
        - Status options: Student, Employed, Unemployed, Retired, Unknown (default)
        - Search operations are case-insensitive
        - Contact IDs are automatically generated when creating new contacts
        - Edit operations maintain data integrity by rolling back failed updates
    """

    name: str | None = None
    view_limit: int = 10
    contacts: dict[str, Contact] = field(default_factory=dict)

    def __post_init__(self):
        super().__init__(self.name)

    def get_state(self) -> dict[str, Any]:
        return get_state_dict(self, ["contacts", "view_limit"])

    def load_state(self, state_dict: dict[str, Any]):
        self.load_contacts_from_dict(state_dict["contacts"])
        self.view_limit = state_dict["view_limit"]

    def load_contacts_from_dict(self, contacts_dict):
        for contact_id, contact_data in contacts_dict.items():
            contact = Contact(
                first_name=contact_data.get("first_name", ""),
                last_name=contact_data.get("last_name", ""),
                contact_id=contact_data.get("contact_id", uuid.uuid4().hex),
                is_user=contact_data.get("is_user", False),
                gender=Gender(contact_data.get("gender", "Unknown")),
                age=contact_data.get("age", 0),
                nationality=contact_data.get("nationality", ""),
                city_living=contact_data.get("city_living", ""),
                country=contact_data.get("country", ""),
                status=Status(contact_data.get("status", "Unknown")),
                job=contact_data.get("job", ""),
                description=contact_data.get("description", ""),
                phone=contact_data.get("phone", ""),
                email=contact_data.get("email", ""),
                address=contact_data.get("address", ""),
            )
            self.contacts[contact_id] = contact

    def reset(self):
        super().reset()
        self.contacts = {}

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_contacts(self, offset: int = 0) -> dict[str, Any]:
        """
        Gets the list of contacts starting from a specified offset. There is a view limit. Use offset to scroll through the contacts.
        :param offset: starting point to retrieve contacts from, default is 0.
        :returns: list of contacts, limited to the specified offset and limit view, with additional metadata about the range of contacts retrieved and total number of contacts
        """
        contacts = list(self.contacts.values())[offset : offset + self.view_limit]
        return {
            "contacts": contacts,
            "metadata": {
                "range": (
                    offset,
                    min(offset + self.view_limit, len(list(self.contacts.values()))),
                ),
                "total": len(list(self.contacts.values())),
            },
        }

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_contact(self, contact_id: str) -> Contact:
        """
        Gets a specific contact by contact_id.
        :param contact_id: ID of the contact to retrieve
        :returns: contact details, if contact_id exists, otherwise raise KeyError
        """
        if contact_id in self.contacts:
            return self.contacts[contact_id]
        else:
            raise KeyError(f"Contact {contact_id} does not exist.")

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_current_user_details(self) -> Contact:
        """
        Gets the current user's details including name, phone number, email address, nationality, country living.
        :returns: Contact details of the current user, if current user details exist in App, otherwise raise KeyError
        """
        for _, contact in self.contacts.items():
            if contact.is_user:
                return contact
        raise KeyError("User Contact does not exist.")

    @type_check
    @event_registered(operation_type=OperationType.WRITE)
    def add_contact(self, contact: Contact) -> str:
        """
        Adds a new contact to the contacts dictionary.
        :param contact: contact to add
        """
        self.contacts[contact.contact_id] = contact
        return contact.contact_id

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_new_contact(
        self,
        first_name: str,
        last_name: str,
        gender: str | None = None,
        age: int | None = None,
        nationality: str | None = None,
        city_living: str | None = None,
        country: str | None = None,
        status: str | None = None,
        job: str | None = None,
        description: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
    ) -> str:
        """
        Adds a new contact to the contacts app.
        :param first_name: first name of the contact, required
        :param last_name: last name of the contact, required
        :param gender: gender of the contact (Male, Female, Other, Unknown), optional default is Unknown
        :param age: age of the contact, optional
        :param nationality: nationality of the contact, optional
        :param city_living: city where the contact is living, optional
        :param country: country where the contact is living, optional
        :param status: status of the contact (Student, Employed, Unemployed, Retired, Unknown), optional default is Unknown
        :param job: job of the contact, optional
        :param description: description of the contact, optional
        :param phone: phone number of the contact, optional
        :param email: email address of the contact, optional
        :param address: address of the contact, optional
        :returns: contact_id of the newly added contact
        """
        names_to_id = {
            c.first_name.lower() + " " + c.last_name.lower(): c.contact_id
            for c in list(self.contacts.values())
        }
        key = first_name.lower() + " " + last_name.lower()
        if key in names_to_id:
            raise ValueError(
                f"Contact already exists with contact id - {names_to_id[key]}."
            )
        if gender is not None:
            new_gender = Gender(gender)
        else:
            new_gender = Gender.UNKNOWN

        if status is not None:
            new_status = Status(status)
        else:
            new_status = Status.UNKNOWN

        contact = Contact(
            contact_id=uuid_hex(self.rng),
            first_name=first_name,
            last_name=last_name,
            gender=new_gender,
            age=age,
            nationality=nationality,
            city_living=city_living,
            country=country,
            status=new_status,
            job=job,
            description=description,
            phone=phone,
            email=email,
            address=address,
        )
        self.contacts[contact.contact_id] = contact
        return contact.contact_id

    def add_contacts(self, contacts: list[Contact]) -> None:
        """
        Adds new contacts to the contacts dictionary.
        """
        for contact in contacts:
            self.contacts[contact.contact_id] = contact

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def edit_contact(self, contact_id: str, updates: dict[str, Any]) -> str | None:
        """
        Edits specific fields of a contact by contact_id.
        :param contact_id: ID of the contact to edit
        :param updates: dictionary of updates to apply to the contact
        :returns: Success message if contact is edited successfully, otherwise raise KeyError or AttributeError
        """
        if contact_id in self.contacts:
            old_contact = copy.deepcopy(self.contacts[contact_id])
            contact = self.contacts[contact_id]
            for key, value in updates.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
                else:
                    raise AttributeError(f"{key} is not a valid attribute of Contact.")
            try:
                contact.__post_init__()  # Validate updated fields
                self.contacts[contact_id] = contact
                return f"Contact {contact_id} updated successfully."
            except Exception as e:
                self.contacts[contact_id] = old_contact
                raise e
        else:
            raise KeyError("Contact does not exist.")

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def delete_contact(self, contact_id: str) -> str:
        """
        Deletes a specific contact by contact_id.
        :param contact_id: ID of the contact to delete
        :returns: Success message if contact is deleted successfully, otherwise raise KeyError
        """
        if contact_id in self.contacts:
            del self.contacts[contact_id]
            return f"Contact {contact_id} successfully deleted."
        else:
            raise KeyError("Contact does not exist.")

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_contacts(self, query: str) -> list[Contact]:
        """
        Searches for contacts based on a query string.
        The search looks for partial matches in first name, last name, phone number, and email.
        :param query: The search query string
        :returns: A list of matching Contact objects
        """
        query = query.lower()
        results = []

        for contact in self.contacts.values():
            if (
                query in contact.first_name.lower()
                or query in contact.last_name.lower()
                or (contact.phone is not None and query in contact.phone.lower())
                or (contact.email is not None and query in contact.email.lower())
                or query in contact.first_name.lower() + " " + contact.last_name.lower()
                or query in contact.last_name.lower() + " " + contact.first_name.lower()
            ):
                results.append(contact)
        return results


@dataclass
class Contacts(ContactsApp):
    __doc__ = ContactsApp.__doc__
    name: str | None = "Contacts"


@dataclass
class InternalContacts(ContactsApp):
    """
    This is where the full set of personas of the universe and their contact information is stored.
    This is not visible to anntators but is part of the universe definition
    """

    name: str | None = "InternalContacts"
