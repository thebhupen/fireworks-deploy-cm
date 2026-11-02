# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import os
import random
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

from jinja2 import Environment, Template, meta

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.calendar import CalendarApp
from are.simulation.apps.contacts import Contact, ContactsApp, Gender
from are.simulation.apps.messaging import Message, MessagingApp
from are.simulation.scenarios.utils.personalization.types import UserContext
from are.simulation.types import Event

random.seed(33)


def jinja_format(template: str, skip_validation: bool = True, **kwargs: Any) -> str:
    if not skip_validation:
        variables = meta.find_undeclared_variables(Environment().parse(template))
        if not all(k in kwargs for k in variables):
            raise ValueError(
                f"Expected: {variables}, got: {sorted(kwargs)}.\nTemplate:\n{template}"
            )
        kwargs = {k: kwargs[k] for k in variables}
    return Template(template, keep_trailing_newline=True).render(**kwargs)


def _parse_timestamp(date_string, date_format="%Y-%m-%d %H:%M") -> datetime:
    """
    Parse a date string into a datetime object.
    If the date string is not in the expected format, return the current time.
    Args:
        date_string: date string to parse
        date_format: format of the date string
    Returns:
        datetime object
    """
    try:
        date = datetime.strptime(date_string, date_format)
        return date
    except ValueError:
        print(f"Invalid date format. Please use {date_format}.")
        return datetime.now(timezone.utc)


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def load_context(path: str) -> UserContext:
    user_context = _load_json(os.path.join(path, "user_context.json"))
    user_context = UserContext(**user_context)
    # Preprocess conversations
    user_name = (
        user_context.profile["first_name"] + " " + user_context.profile["last_name"]
    )
    for c in user_context.conversations:
        c["participants"] = c["participants"].split(", ")
        for m in c["conversation"]:
            if m["sender"] not in c["participants"]:
                c["participants"].append(m["sender"])
            if m["sender"] == user_name:
                m["sender"] = "Me"
        if user_name in c["participants"]:
            c["participants"].remove(user_name)
    return user_context


def profile_to_contact(profile: dict[str, Any]) -> Contact:
    """
    Convert a profile dictionary to a Contact object.
    Args:
        profile: dictionary containing the profile information
    Returns:
        Contact object
    """
    return Contact(
        first_name=profile["first_name"],
        last_name=profile["last_name"],
        age=profile["age"],
        gender=Gender.FEMALE if profile["gender"] == "female" else Gender.MALE,
        nationality=profile["nationality"],
        city_living=profile["place_of_residence"],
        job=profile["job"],
        description=profile["description"],
        phone=profile["phone_number"],
        email=profile["email"],
    )


def populate_contatcs(context: UserContext, contacts: ContactsApp) -> ContactsApp:
    """
    Populate contacts app with user and relation profiles.
    Args:
        context: user context containing the profile and relation profiles
        contacts: contacts app
    Returns:
        Contacts app with user and relation profiles populated
    """
    # user contact
    contact = profile_to_contact(context.profile)
    contact = replace(contact, first_name="Me", last_name="")
    contacts.add_contact(contact)
    # other contacts
    for profile in context.relation_profiles:
        contact = profile_to_contact(profile)
        contacts.add_contact(contact)
    return contacts


def populate_messaging(context: UserContext, messaging: MessagingApp) -> MessagingApp:
    """
    Populate messaging app with user conversations.
    Args:
        context: user context containing the profile and relation profiles
        messaging: messaging app
    Returns:
        Messaging app with conversations populated
    """

    def add_message(conversation_id: str, sender: str, content: str, timestamp: float):
        messaging.conversations[conversation_id].messages.append(  # type: ignore
            Message(
                message_id=uuid.uuid4().hex,
                sender=sender,
                timestamp=timestamp,
                content=content,
            )
        )
        messaging.conversations[conversation_id].update_last_updated(timestamp)

    for conv in context.conversations:
        conv_id = messaging.create_conversation(
            participants=conv["participants"], title=conv["title"]
        )
        for msg in conv["conversation"]:
            add_message(
                conversation_id=conv_id,
                sender=msg["sender"],
                content=msg["message"],
                timestamp=_parse_timestamp(msg["timestamp"]).timestamp(),
            )
    return messaging


def populate_calendar(context: UserContext, calendar: CalendarApp) -> CalendarApp:
    """
    Populate calendar app with user events.
    Args:
        context: user context containing the profile and relation profiles
        calendar: calendar app
    Returns:
        Calendar app with events populated
    """
    for event in context.events:
        start_datetime = _parse_timestamp(event["timestamp"])
        end_datetime = min(
            start_datetime + timedelta(hours=1),
            start_datetime.replace(hour=23, minute=59, second=59),
        )
        calendar.add_calendar_event(
            title=event["title"],
            start_datetime=start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            end_datetime=end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            tag=event["category"],
            description=event["content"],
            location=event["location"],
            attendees=[a for a in event["participants"].split(", ") if a != "None"],
        )
    return calendar


def populate_apps(
    context: UserContext,
    contacts: ContactsApp | None = None,
    messaging: MessagingApp | None = None,
    calendar: CalendarApp | None = None,
) -> None:
    """
    Populate apps with user context.
    Args:
        context: user context containing the profile and relation profiles
        contacts: contacts app
        messaging: messaging app
        calendar: calendar app
    Returns:
        Tuple of contacts, messaging, and calendar apps with user context populated
    """
    if contacts is not None:
        contacts = populate_contatcs(context, contacts)
    if messaging is not None:
        messaging = populate_messaging(context, messaging)
    if calendar is not None:
        calendar = populate_calendar(context, calendar)


def schedule_noise_conversations(
    context: UserContext,
    messaging: MessagingApp,
    base_event: Event | None = None,
) -> list[Event]:
    """
    Schedule noise conversations between the user and other contacts.
    Args:
        context: user context containing the conversations
        messaging: messaging app
        base_event: base event to schedule the noise conversations after
    Returns:
        List of events representing the noise conversations
    """
    messages = []
    for conv in context.conversations:
        conv_id = messaging.create_conversation(participants=conv["participants"])
        _messages = [base_event]
        for msg in conv["conversation"]:
            if msg["sender"] == "Me":
                event = Event.from_function(
                    messaging.send_message,
                    conversation_id=conv_id,
                    content=msg["message"],
                )
            else:
                event = Event.from_function(
                    messaging.add_message,
                    conversation_id=conv_id,
                    sender=msg["sender"],
                    content=msg["message"],
                )
            random.randint(3, 5)
            event.depends_on(_messages[-1], delay_seconds=2)
            _messages.append(event)
        messages.extend(_messages[1:])
    return messages


def schedule_noise_assistant_calls(
    context: UserContext,
    aui: AgentUserInterface,
    num_calls: int = 3,
    min_time_between_calls: int = 3,
    max_time_between_calls: int = 5,
    base_event: Event | None = None,
) -> list[Event]:
    """
    Schedule noise assistant calls between the user and other contacts.
    It will cycles over the assistant calls in the context until it reaches the number of calls.
    Args:
        context: user context containing assistant calls
        aui: agent user interface
        num_calls: number of noise assistant calls to schedule
        min_time_between_calls: minimum time between noise assistant calls
        base_event: base event to schedule the noise assistant calls after
    Returns:
        List of events representing the noise assistant calls
    """
    calls = []
    for i in range(num_calls):
        call_idx = i % len(context.assistant_calls)
        event = Event.from_function(
            aui.send_message_to_agent,
            content=context.assistant_calls[call_idx],
        )
        delay = random.randint(min_time_between_calls, max_time_between_calls)
        event.depends_on(calls[-1] if calls else None, delay_seconds=delay)
        calls.append(event)
    return calls


def profile_as_text(
    profile, hidden_attributes=["phone_number", "email", "social_security"]
) -> str:
    return "\n".join(
        f"- {k.replace('_', ' ')}: {v}"
        for k, v in profile.items()
        if k not in hidden_attributes
    )


def relation_as_text(relation) -> str:
    relation_text = []
    for r in relation:
        _r = f" - {r['first_name']} {r['last_name']}: {r['relationship_description']}"
        relation_text.append(_r)
    return "\n".join(relation_text)
