# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import uuid

import pytest

from are.simulation.apps.contacts import Contact, ContactsApp, Gender, Status
from are.simulation.environment import Environment


def dummy_populate(app):
    contact_0 = Contact(
        first_name="John",
        last_name="Doe",
        gender=Gender.MALE,
        age=30,
        nationality="American",
        city_living="New York",
        status=Status.EMPLOYED,
        job="Software Developer",
        description="A software developer living in New York.",
        phone="+1 555 555 5555",
        email="johndoe@gmail.com",
    )

    contact_0_dict = vars(contact_0)

    contact_1 = Contact(**contact_0_dict)
    contact_1.first_name = "Jane"
    contact_1.contact_id = "0"

    contact_2 = Contact(**contact_0_dict)
    contact_2.first_name = "Jack"
    contact_2.contact_id = "1"

    contact_3 = Contact(**contact_0_dict)
    contact_3.first_name = "Jill"
    contact_3.contact_id = "2"

    contact_4 = Contact(**contact_0_dict)
    contact_4.first_name = "Jim"
    contact_4.contact_id = "3"

    contact_5 = Contact(**contact_0_dict)
    contact_5.first_name = "Jenny"
    contact_5.contact_id = "4"

    app.add_contact(contact_0)
    app.add_contact(contact_1)
    app.add_contact(contact_2)
    app.add_contact(contact_3)
    app.add_contact(contact_4)
    app.add_contact(contact_5)


def test_send_init():
    app = ContactsApp()
    environment = Environment()
    environment.register_apps([app])
    assert len(app.contacts) == 0


def test_add_contact():
    app = ContactsApp()
    environment = Environment()
    environment.register_apps([app])
    contact = Contact(
        contact_id=uuid.uuid4().hex,
        first_name="John",
        last_name="Doe",
        gender=Gender.MALE,
        age=30,
        nationality="American",
        city_living="New York",
        status=Status.EMPLOYED,
        job="Software Developer",
        description="A software developer living in New York.",
        phone="+1 555 555 5555",
        email="johndoe@gmail.com",
    )
    key = app.add_contact(contact)
    assert len(app.contacts) == 1
    assert app.contacts[key].first_name == "John"
    assert app.contacts[key].last_name == "Doe"
    assert app.contacts[key].gender == Gender.MALE
    assert app.contacts[key].age == 30
    assert app.contacts[key].nationality == "American"
    assert app.contacts[key].city_living == "New York"
    assert app.contacts[key].status == Status.EMPLOYED
    assert app.contacts[key].job == "Software Developer"
    assert app.contacts[key].description == "A software developer living in New York."
    assert app.contacts[key].phone == "+1 555 555 5555"
    assert app.contacts[key].email == "johndoe@gmail.com"


def test_get_contacts():
    app = ContactsApp()
    app.view_limit = 5
    environment = Environment()
    environment.register_apps([app])

    dummy_populate(app)

    assert len(app.contacts) == 6
    assert len(app.get_contacts()["contacts"]) == 5
    assert len(app.get_contacts(1)["contacts"]) == 5
    assert len(app.get_contacts(3)["contacts"]) == 3


def test_delete_contact():
    app = ContactsApp()
    environment = Environment()
    environment.register_apps([app])

    dummy_populate(app)

    assert len(app.contacts) == 6
    app.delete_contact(list(app.contacts.keys())[0])
    assert len(app.contacts) == 5
    app.delete_contact(list(app.contacts.keys())[0])
    assert len(app.contacts) == 4
    app.delete_contact(list(app.contacts.keys())[0])
    assert len(app.contacts) == 3


def test_edit_contact():
    app = ContactsApp()
    environment = Environment()
    environment.register_apps([app])

    dummy_populate(app)

    updates = {
        "first_name": "Gael",
        "last_name": "Gouzerch",
        "age": 27,
        "gender": "Female",
        "job": "Pro E-sport Player",
    }
    key = list(app.contacts.keys())[0]
    app.edit_contact(key, updates)
    assert app.contacts[key].first_name == "Gael"
    assert app.contacts[key].last_name == "Gouzerch"
    assert app.contacts[key].age == 27
    assert app.contacts[key].job == "Pro E-sport Player"
    assert app.contacts[key].gender == Gender.FEMALE


def test_add_new_contact():
    app = ContactsApp()
    environment = Environment()
    environment.register_apps([app])

    # Test adding a contact with all fields filled in
    key = app.add_new_contact(
        first_name="John",
        last_name="Doe",
        gender="Male",
        age=30,
        nationality="American",
        city_living="New York",
        status="Employed",
        job="Software Developer",
        description="A software developer living in New York.",
        phone="+1 555 555 5555",
        email="johndoe@gmail.com",
    )
    assert len(app.contacts) == 1
    assert app.contacts[key].first_name == "John"
    assert app.contacts[key].last_name == "Doe"
    assert app.contacts[key].gender == Gender.MALE
    assert app.contacts[key].age == 30
    assert app.contacts[key].nationality == "American"
    assert app.contacts[key].city_living == "New York"
    assert app.contacts[key].status == Status.EMPLOYED
    assert app.contacts[key].job == "Software Developer"
    assert app.contacts[key].description == "A software developer living in New York."
    assert app.contacts[key].phone == "+1 555 555 5555"
    assert app.contacts[key].email == "johndoe@gmail.com"

    # Test adding a contact with only required fields filled in
    key_1 = app.add_new_contact(first_name="Jane", last_name="Doe")
    assert len(app.contacts) == 2
    assert app.contacts[key_1].first_name == "Jane"
    assert app.contacts[key_1].last_name == "Doe"
    assert app.contacts[key_1].gender is Gender.UNKNOWN
    assert app.contacts[key_1].age is None
    assert app.contacts[key_1].nationality is None
    assert app.contacts[key_1].city_living is None
    assert app.contacts[key_1].status == Status.UNKNOWN
    assert app.contacts[key_1].job is None
    assert app.contacts[key_1].description is None
    assert app.contacts[key_1].phone is None
    assert app.contacts[key_1].email is None

    # Test adding a contact with invalid input
    with pytest.raises(ValueError):
        app.add_new_contact(first_name="John", last_name="Doe", gender="invalid")


def test_validate_enum_field_helper():
    """Test the _validate_enum_field helper method with various input formats."""
    contact = Contact(first_name="Test", last_name="User")

    assert contact._validate_enum_field(Gender.MALE, Gender) == Gender.MALE
    assert contact._validate_enum_field("Female", Gender) == Gender.FEMALE
    assert contact._validate_enum_field("FEMALE", Gender) == Gender.FEMALE
    assert contact._validate_enum_field("female", Gender) == Gender.FEMALE
    assert contact._validate_enum_field("Gender.OTHER", Gender) == Gender.OTHER
    assert contact._validate_enum_field("Gender.Other", Gender) == Gender.OTHER
    assert contact._validate_enum_field("MALE", Gender) == Gender.MALE
    assert contact._validate_enum_field("Male", Gender) == Gender.MALE
    assert contact._validate_enum_field("Employed", Status) == Status.EMPLOYED
    assert contact._validate_enum_field("EMPLOYED", Status) == Status.EMPLOYED
    assert contact._validate_enum_field("Status.STUDENT", Status) == Status.STUDENT

    with pytest.raises(ValueError):
        contact._validate_enum_field("InvalidGender", Gender)
    with pytest.raises(ValueError):
        contact._validate_enum_field("Gender.INVALID", Gender)
    with pytest.raises(ValueError):
        contact._validate_enum_field(123, Gender)


def test_contact_creation_with_enum_validation():
    """Test that Contact creation properly validates enums using the helper method."""

    # Test all case variations work in contact creation
    contact1 = Contact(
        first_name="John",
        last_name="Doe",
        gender="Gender.Male",  # type: ignore
        status="Status.Employed",  # type: ignore
    )
    assert contact1.gender == Gender.MALE and contact1.status == Status.EMPLOYED

    contact2 = Contact(
        first_name="Jane",
        last_name="Smith",
        gender="FEMALE",  # type: ignore
        status="STUDENT",  # type: ignore
    )
    assert contact2.gender == Gender.FEMALE and contact2.status == Status.STUDENT

    contact3 = Contact(
        first_name="Bob",
        last_name="Wilson",
        gender="male",  # type: ignore
        status="retired",  # type: ignore
    )
    assert contact3.gender == Gender.MALE and contact3.status == Status.RETIRED

    contact4 = Contact(
        first_name="Alice",
        last_name="Johnson",
        gender=Gender.OTHER,
        status=Status.UNEMPLOYED,
    )
    assert contact4.gender == Gender.OTHER and contact4.status == Status.UNEMPLOYED

    # Invalid inputs should raise ValueError
    with pytest.raises(ValueError):
        Contact(first_name="Invalid", last_name="User", gender="InvalidGender")  # type: ignore
    with pytest.raises(ValueError):
        Contact(first_name="Invalid", last_name="User", status="InvalidStatus")  # type: ignore
