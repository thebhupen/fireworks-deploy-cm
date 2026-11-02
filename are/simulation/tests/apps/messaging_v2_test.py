# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import datetime
import re
import time
from unittest.mock import MagicMock

import pytest

from are.simulation.apps.messaging_v2 import (
    FileMessageV2,
    MessageV2,
    MessagingAppMode,
    MessagingAppV2,
)
from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.environment import Environment
from are.simulation.tests.utils import IN_GITHUB_ACTIONS

from .utils import get_timestamp


def test_init_app():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}


def test_create_conversations():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["test1", "test2", "test3"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    app.create_group_conversation(
        user_ids=app.get_user_ids(["test1", "test2"]),
        title="test title",
    )
    assert len(app.conversations) == 1
    conv_key = next(iter(app.conversations))
    conversation = app.conversations[conv_key]

    assert conversation.title == "test title"
    assert "test1" in app.get_user_names(conversation.participant_ids)
    assert "test2" in app.get_user_names(conversation.participant_ids)
    assert conversation.title == "test title"
    assert re.match(r"^[a-f0-9]{32}$", conversation.conversation_id) is not None
    assert re.match(r"^.*\(last updated: .*\)$", conversation.summary) is not None

    app.send_message(
        user_id=app.get_user_id("test3"),
        content="test message",
    )

    app.send_message(
        user_id=app.get_user_id("test3"),
        content="",
    )

    assert len(app.conversations) == 2


def test_create_conversations_phone_number():
    app = MessagingAppV2(
        current_user_id="42", current_user_name="Me", mode=MessagingAppMode.PHONE_NUMBER
    )
    app.add_contacts([("test1", "123"), ("test2", "234")])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    conv_id = app.create_group_conversation(
        user_ids=app.get_user_ids(["test1", "test2"]),
        title="test title",
    )
    assert len(app.conversations) == 1
    conversation = app.conversations[conv_id]

    assert conversation.title == "test title"
    assert "test1" in app.get_user_names(conversation.participant_ids)
    assert "test2" in app.get_user_names(conversation.participant_ids)
    assert re.match(r"^[a-f0-9]{32}$", conversation.conversation_id) is not None
    assert re.match(r"^.*\(last updated: .*\)$", conversation.summary) is not None

    # create a conversation with additional phone number not in contacts
    conv_id = app.create_group_conversation(
        user_ids=app.get_user_ids(["test1"]) + ["678"],
        title="test title with phone",
    )
    assert len(app.conversations) == 2
    conversation = app.conversations[conv_id]

    assert conversation.title == "test title with phone"
    assert "test1" in app.get_user_names(conversation.participant_ids)
    assert "678" in conversation.participant_ids
    assert re.match(r"^[a-f0-9]{32}$", conversation.conversation_id) is not None
    assert re.match(r"^.*\(last updated: .*\)$", conversation.summary) is not None

    app.send_message(
        user_id=app.get_user_id("test1"),
        content="test message",
    )

    app.send_message(
        user_id="33",
        content="another test message",
    )

    assert len(app.conversations) == 4


def test_create_group_conversation_with_no_participants():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    with pytest.raises(Exception):
        app.create_group_conversation(
            user_ids=[],
            title="test title",
        )


def test_create_group_conversation_with_one_participants():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    with pytest.raises(Exception):
        app.create_group_conversation(
            user_ids=["33"],
            title="test title",
        )


def test_create_group_conversation_with_no_title():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["test1", "test2"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    app.create_group_conversation(
        user_ids=app.get_user_ids(["test1", "test2"]),
    )
    assert len(app.conversations) == 1
    conv_key = next(iter(app.conversations))
    conversation = app.conversations[conv_key]

    assert "test1" in conversation.title  # type: ignore
    assert "test2" in conversation.title  # type: ignore


def test_list_all_conversations():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Foo",
    )

    assert len(app.conversations) == 1

    # create a conversation with same people but different title creates a new conversation
    app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Bar",
    )

    assert len(app.conversations) == 2
    res = app.conversations
    assert len(res) == 2


def test_conversation_default_title():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
    )

    app.send_message_to_group_conversation(
        conversation_id=conv_key, content="test message"
    )

    assert len(app.conversations) == 1
    assert len(app.conversations[next(iter(app.conversations))].messages) == 1  # type: ignore
    assert app.conversations[next(iter(app.conversations))].title == "Bar, Foo"  # type: ignore
    assert (
        app.conversations[next(iter(app.conversations))].messages[0].content
        == "test message"
    )  # type: ignore


def test_list_all_conversations_with_no_conversations():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    res = app.conversations
    assert len(res) == 0


def test_list_conversations_by_participants():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar", "Bob"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation with one user
    app.send_message(
        user_id=app.get_user_id("Foo"),
        content="test message",
    )

    # create a conversation
    app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Bar",
    )

    # create a conversation with one user
    app.send_message(
        user_id=app.get_user_id("Bob"),
    )

    res = app.list_conversations_by_participant(app.get_user_id("Foo"))
    assert len(res) == 2

    res = app.list_conversations_by_participant(app.get_user_id("Bar"))
    assert len(res) == 1

    res = app.list_conversations_by_participant(app.get_user_id("Me"))
    assert len(res) == len(app.conversations)


def test_send_message_to_group_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Foo",
    )

    app.add_message(conv_key, app.get_user_id("Foo"), "Hello")
    app.add_message(conv_key, app.get_user_id("Bar"), "Hi")
    app.add_message(conv_key, app.get_user_id("Foo"), "I want 💵🏠")

    assert len(app.conversations) == 1  # type: ignore

    assert len(app.conversations[conv_key].messages) == 3  # type: ignore

    app.send_message_to_group_conversation(
        conversation_id=conv_key, content="I have lots of 💵💵💵"
    )

    assert len(app.conversations[conv_key].messages) == 4  # type: ignore
    assert app.conversations[conv_key].messages[-1].content == "I have lots of 💵💵💵"  # type: ignore
    assert app.conversations[conv_key].messages[-1].sender_id == app.current_user_id  # type: ignore


def test_send_message_to_group_conversation_but_to_one_one_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a 1:1 conversation
    conv_key = app.send_message(
        user_id=app.get_user_id("Foo"),
        content="Hello",
    )

    # attempts to send a group message to a 1:1 conversation
    with pytest.raises(Exception):
        app.send_message_to_group_conversation(
            conversation_id=conv_key, content="Hey, is it a group conversation?"
        )


def test_send_message_to_group_conversation_with_no_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    with pytest.raises(Exception):
        app.send_message_to_group_conversation(
            conversation_id="123", content="I have lots of 💵💵💵"
        )


def test_read_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Foo",
    )

    conv_key = next(iter(app.conversations))

    for i in range(20):
        app.add_message(conv_key, app.get_user_id("Foo"), f"{i}")
        # To make sure the messages are added with reasonable timestamps
        time.sleep(0.1)

    assert len(app.conversations) == 1  # type: ignore
    conv_size = len(app.conversations[conv_key].messages)  # type: ignore
    res = app.read_conversation(conversation_id=conv_key)
    for i in range(10):
        assert res["messages"][i].content == str(conv_size - i - 1)  # type: ignore

    for i in range(20):
        res = app.read_conversation(conversation_id=conv_key, offset=i)
        assert len(res["messages"]) == min(10, 20 - i)  # type: ignore


def test_send_attachment():
    # Setup env with fs
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    fs = SandboxLocalFileSystem()
    if not fs.exists("source_dir"):
        fs.mkdir("source_dir")
    if not fs.exists("download_dir"):
        fs.mkdir("download_dir")
    with fs.open("source_dir/test_write.txt", "w") as file:
        file.write("test with emojis 💵💵💵💵💵💵💵💵💵💵💵�")

    environment = Environment()
    environment.register_apps([app, fs])

    assert fs.exists("source_dir/test_write.txt")
    assert fs.exists("download_dir")

    # create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Foo, Bar and Me",
    )

    app.add_message(conv_key, app.get_user_id("Foo"), "Hello")
    app.add_message(conv_key, app.get_user_id("Bar"), "dnejfi dweodna asxs")

    app.send_message_to_group_conversation(conv_key, "I have lots of 💵💵💵")

    _output = app.send_message_to_group_conversation(
        conv_key,
        content="",
        attachment_path="source_dir/test_write.txt",
    )

    # msg_id = output["message_id"]

    assert isinstance(app.conversations[conv_key].messages[-1], FileMessageV2)  # type: ignore

    msg_id = app.conversations[conv_key].messages[-1].message_id  # type: ignore

    app.download_attachment(conv_key, msg_id, "download_dir")

    assert fs.exists("download_dir/test_write.txt")

    original_contnet = fs.open("source_dir/test_write.txt").read()
    downloaded_content = fs.open("download_dir/test_write.txt").read()

    assert original_contnet == downloaded_content


def test_list_conversations_ordered_by_most_recent():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # Set the view limit for testing
    app.conversation_view_limit = 2

    # Create multiple conversations with different last_updated times
    conv_key1 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]), title="Conversation 1"
    )
    app.conversations[conv_key1].last_updated = (
        datetime.datetime.now().timestamp() - 10000
    )  # Older

    app.conversations[conv_key1].messages.extend(
        [
            MessageV2(
                sender_id=app.get_user_id("Alice"),
                content="Alice message 1",
            ),
            MessageV2(
                sender_id=app.get_user_id("Bob"),
                content="Bob message 1",
            ),
            MessageV2(
                sender_id=app.get_user_id("Alice"),
                content="Alice message 2",
            ),
            MessageV2(
                sender_id=app.get_user_id("Bob"),
                content="Bob message 2",
            ),
        ]
    )

    conv_key2 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Charlie", "Dave"]), title="Conversation 2"
    )

    app.conversations[
        conv_key2
    ].last_updated = datetime.datetime.now().timestamp()  # Most recent

    app.conversations[conv_key2].messages.extend(
        [
            MessageV2(
                sender_id=app.get_user_id("Charlie"),
                content="Charlie message 1",
            ),
            MessageV2(
                sender_id=app.get_user_id("Dave"),
                content="Dave message 1",
            ),
            MessageV2(
                sender_id=app.get_user_id("Charlie"),
                content="Charlie message 2",
            ),
            MessageV2(
                sender_id=app.get_user_id("Dave"),
                content="Dave message 2",
            ),
        ]
    )

    conv_key3 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Eve", "Frank"]), title="Conversation 3"
    )
    app.conversations[conv_key3].last_updated = (
        datetime.datetime.now().timestamp() - 100
    )  # Middle

    app.conversations[conv_key3].messages.extend(
        [
            MessageV2(
                sender_id=app.get_user_id("Eve"),
                content="Eve message 1",
            ),
            MessageV2(
                sender_id=app.get_user_id("Frank"),
                content="Frank message 1",
            ),
            MessageV2(
                sender_id=app.get_user_id("Eve"),
                content="Eve message 2",
            ),
            MessageV2(
                sender_id=app.get_user_id("Frank"),
                content="Frank message 2",
            ),
        ]
    )

    # Test without offset
    recent_conversations = app.list_recent_conversations(
        offset=0,
        limit=2,
        offset_recent_messages_per_conversation=0,
        limit_recent_messages_per_conversation=1,
    )
    assert len(recent_conversations) == 2  # Should respect the view limit
    assert recent_conversations[0].conversation_id == conv_key2  # Most recent
    assert recent_conversations[1].conversation_id == conv_key3  # Second most recent
    assert len(recent_conversations[0].messages) == 1
    assert len(recent_conversations[1].messages) == 1
    assert recent_conversations[0].messages[0].content == "Dave message 2"
    assert recent_conversations[1].messages[0].content == "Frank message 2"

    # Test with offset
    recent_conversations_offset = app.list_recent_conversations(
        offset=1,
        limit=2,
        offset_recent_messages_per_conversation=0,
        limit_recent_messages_per_conversation=5,
    )
    assert len(recent_conversations_offset) == 2  # Should respect the view limit
    assert (
        recent_conversations_offset[0].conversation_id == conv_key3
    )  # Second most recent
    assert recent_conversations_offset[1].conversation_id == conv_key1  # Oldest
    assert len(recent_conversations_offset[0].messages) == 4
    assert len(recent_conversations_offset[1].messages) == 4

    # Test with offset on messages
    recent_conversations_offset = app.list_recent_conversations(
        offset=1,
        limit=2,
        offset_recent_messages_per_conversation=1,
        limit_recent_messages_per_conversation=5,
    )
    assert len(recent_conversations_offset) == 2  # Should respect the view limit
    assert (
        recent_conversations_offset[0].conversation_id == conv_key3
    )  # Second most recent
    assert recent_conversations_offset[1].conversation_id == conv_key1  # Oldest
    assert len(recent_conversations_offset[0].messages) == 3
    assert len(recent_conversations_offset[1].messages) == 3
    assert recent_conversations_offset[0].messages[0].content == "Eve message 2"
    assert recent_conversations_offset[0].messages[1].content == "Frank message 1"
    assert recent_conversations_offset[0].messages[2].content == "Eve message 1"
    assert recent_conversations_offset[1].messages[0].content == "Alice message 2"
    assert recent_conversations_offset[1].messages[1].content == "Bob message 1"
    assert recent_conversations_offset[1].messages[2].content == "Alice message 1"

    # Test with offset that exceeds the number of conversations
    recent_conversations_excess_offset = app.list_recent_conversations(
        offset=3, limit=2
    )
    assert (
        len(recent_conversations_excess_offset) == 0
    )  # No conversations should be returned


def test_add_participant_to_conversation_success():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]), title="Test Conversation"
    )
    assert len(app.conversations[conv_key].participant_ids) == 3  # Includes "Me"

    # Add a new participant
    app.add_participant_to_conversation(
        conversation_id=conv_key, user_id=app.get_user_id("Charlie")
    )
    assert app.get_user_id("Charlie") in app.conversations[conv_key].participant_ids
    assert len(app.conversations[conv_key].participant_ids) == 4
    assert app.conversations[conv_key].title == "Test Conversation"


def test_add_participant_to_conversation_with_default_title_success():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"])
    )
    assert len(app.conversations[conv_key].participant_ids) == 3  # Includes "Me"
    assert app.conversations[conv_key].title == app.get_default_title(
        app.conversations[conv_key].participant_ids
    )

    # Add a new participant
    app.add_participant_to_conversation(
        conversation_id=conv_key, user_id=app.get_user_id("Charlie")
    )
    assert app.get_user_id("Charlie") in app.conversations[conv_key].participant_ids
    assert len(app.conversations[conv_key].participant_ids) == 4
    assert app.conversations[conv_key].title == app.get_default_title(
        app.conversations[conv_key].participant_ids
    )


def test_add_participant_to_nonexistent_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Attempt to add a participant to a non-existent conversation
    with pytest.raises(Exception):
        app.add_participant_to_conversation(
            conversation_id="nonexistent_id", user_id=app.get_user_id("Charlie")
        )


def test_add_existing_participant_to_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]), title="Test Conversation"
    )
    assert len(app.conversations[conv_key].participant_ids) == 3  # Includes "Me"

    # Attempt to add an existing participant
    with pytest.raises(Exception):
        app.add_participant_to_conversation(
            conversation_id=conv_key, user_id=app.get_user_id("Alice")
        )


def test_remove_participant_from_conversation_success():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]), title="Test Conversation"
    )
    assert len(app.conversations[conv_key].participant_ids) == 3  # Includes "Me"

    # Remove a participant
    app.remove_participant_from_conversation(
        conversation_id=conv_key, user_id=app.get_user_id("Alice")
    )
    assert "Alice" not in app.conversations[conv_key].participant_ids
    assert len(app.conversations[conv_key].participant_ids) == 2
    assert app.conversations[conv_key].title == "Test Conversation"


def test_remove_participant_from_conversation_with_default_title_success():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"])
    )
    assert len(app.conversations[conv_key].participant_ids) == 3  # Includes "Me"
    assert app.conversations[conv_key].title == app.get_default_title(
        app.conversations[conv_key].participant_ids
    )

    # Remove a participant
    app.remove_participant_from_conversation(
        conversation_id=conv_key, user_id=app.get_user_id("Alice")
    )
    assert "Alice" not in app.conversations[conv_key].participant_ids
    assert len(app.conversations[conv_key].participant_ids) == 2
    assert app.conversations[conv_key].title == app.get_default_title(
        app.conversations[conv_key].participant_ids
    )


def test_remove_participant_from_nonexistent_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Attempt to remove a participant from a non-existent conversation
    with pytest.raises(Exception) as excinfo:
        app.remove_participant_from_conversation(
            conversation_id="nonexistent_id", user_id=app.get_user_id("Charlie")
        )
    assert "Conversation with id nonexistent_id not found" in str(excinfo.value)


def test_remove_nonexistent_participant_from_conversation():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]), title="Test Conversation"
    )
    assert len(app.conversations[conv_key].participant_ids) == 3  # Includes "Me"

    # Attempt to remove a participant who is not in the conversation
    with pytest.raises(Exception) as excinfo:
        app.remove_participant_from_conversation(
            conversation_id=conv_key, user_id=app.get_user_id("Charlie")
        )
    assert f"Participant {app.get_user_id('Charlie')} not in conversation" in str(
        excinfo.value
    )


def test_lookup_user_id():
    app = MessagingAppV2(
        current_user_id="1",
        current_user_name="Me",
        id_to_name={
            "1": "Me",
            "2": "Ayita Kuznetsova",
            "3": "Luzia Barbosa",
            "4": "Luiz Silva",
        },
    )
    matches = app.lookup_user_id("Luzia")
    assert matches == {"Luzia Barbosa": "3"}


def test_search_message():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Foo",
    )

    app.add_message(
        conv_key,
        app.get_user_id("Foo"),
        "Hello",
        get_timestamp("2023-01-01 1:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Bar"),
        "Hi!!!",
        get_timestamp("2023-01-01 2:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Foo"),
        "I want 💵🏠",
        get_timestamp("2023-01-01 3:00:00"),
    )

    assert len(app.conversations) == 1  # type: ignore

    assert len(app.conversations[conv_key].messages) == 3  # type: ignore

    result = app.search(
        query="Hi",
    )

    assert len(result) == 1
    assert result[0] == conv_key

    # with valid date filter
    result = app.search(
        query="Hi",
        min_date="2023-01-01 1:00:00",
        max_date="2023-01-02 0:00:00",
    )

    assert len(result) == 1
    assert result[0] == conv_key

    # with out of range date filter
    result = app.search(
        query="Hi",
        max_date="2023-01-01 1:00:00",
    )

    assert len(result) == 0


def add_non_matching_users(app: MessagingAppV2, mock_uuid) -> None:
    mock_uuid.side_effect = [MagicMock(hex=f"{x}A3") for x in range(100)]
    for id in ["Foo", "Bar"]:
        app.add_users([id])
        tmp_key = app.get_user_id(id)
        # delete if a user matches the regex
        assert re.match(r"C\d{6,}", tmp_key) is None


def test_read_conversation_dates():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Foo",
    )
    app.add_message(
        conv_key,
        app.get_user_id("Foo"),
        "Hello C123",
        get_timestamp("2023-01-01 1:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Bar"),
        "Hi 1324!!!",
        get_timestamp("2023-01-01 2:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Foo"),
        "Goodbye D1234567890",
        get_timestamp("2023-01-01 3:00:00"),
    )

    assert len(app.conversations) == 1  # type: ignore

    assert len(app.conversations[conv_key].messages) == 3  # type: ignore

    result = app.read_conversation(
        conversation_id=conv_key,
        offset=0,
        limit=5,
    )

    assert len(result["messages"]) == 3

    result = app.read_conversation(
        conversation_id=conv_key,
        offset=0,
        limit=5,
        min_date="2023-01-01 1:55:00",
    )
    assert len(result["messages"]) == 2

    result = app.read_conversation(
        conversation_id=conv_key,
        offset=0,
        limit=5,
        max_date="2023-01-01 1:55:00",
    )
    assert len(result["messages"]) == 1
    assert len(result["messages"]) == 1


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="does not work in github actions")
def test_read_conversation_min_date_max_date():
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Foo", "Bar"])
    environment = Environment()
    environment.register_apps([app])
    assert len(environment.apps) == 1
    assert app.conversations == {}

    # create a conversation
    app.create_group_conversation(
        user_ids=app.get_user_ids(["Foo", "Bar"]),
        title="Foo",
    )

    conv_key = next(iter(app.conversations))

    # Create messages with timestamps
    for i in range(5):
        app.create_and_add_message(conv_key, app.get_user_id("Foo"), f"{i}")
        time.sleep(1)

    # Get the timestamps of the first and last messages
    first_message_timestamp = app.conversations[conv_key].messages[0].timestamp
    last_message_timestamp = app.conversations[conv_key].messages[-1].timestamp

    # Test with min_date
    min_date = datetime.datetime.fromtimestamp(
        first_message_timestamp + 2, tz=datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S")

    res = app.read_conversation(conversation_id=conv_key, min_date=min_date)
    assert len(res["messages"]) == 3, f"{len(res['messages'])} != 3"  # type: ignore

    # Test with max_date
    max_date = datetime.datetime.fromtimestamp(
        last_message_timestamp - 2, tz=datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S")
    res = app.read_conversation(conversation_id=conv_key, max_date=max_date)
    assert len(res["messages"]) == 3, f"{len(res['messages'])} != 2"  # type: ignore

    # Test with both min_date and max_date
    res = app.read_conversation(
        conversation_id=conv_key, min_date=min_date, max_date=max_date
    )
    assert len(res["messages"]) == 1  # type: ignore

    # Test with invalid dates
    invalid_min_date = "2022-01-01 00:00:00"
    invalid_max_date = "2024-01-01 00:00:00"
    res = app.read_conversation(
        conversation_id=conv_key, min_date=invalid_min_date, max_date=invalid_max_date
    )
    assert len(res["messages"]) == 0  # type: ignore


def test_regex_search_basic_message_content():
    """Test basic regex search functionality in message content."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversation with messages
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Test Conversation",
    )

    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Hello world!",
        get_timestamp("2023-01-01 1:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Bob"),
        "How are you doing?",
        get_timestamp("2023-01-01 2:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "I'm doing great, thanks!",
        get_timestamp("2023-01-01 3:00:00"),
    )

    # Test exact word match
    result = app.regex_search("Hello")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test partial word match
    result = app.regex_search("world")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test case insensitive match
    result = app.regex_search("HELLO")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test no match
    result = app.regex_search("goodbye")
    assert len(result) == 0


def test_regex_search_regex_patterns():
    """Test regex search with various regex patterns."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversation with messages
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Test Conversation",
    )

    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Call me at 123-456-7890",
        get_timestamp("2023-01-01 1:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Bob"),
        "My email is bob@example.com",
        get_timestamp("2023-01-01 2:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "The meeting is at 3:30 PM",
        get_timestamp("2023-01-01 3:00:00"),
    )

    # Test phone number pattern
    result = app.regex_search(r"\d{3}-\d{3}-\d{4}")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test email pattern
    result = app.regex_search(r"\w+@\w+\.\w+")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test time pattern
    result = app.regex_search(r"\d{1,2}:\d{2}\s*(AM|PM)")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test wildcard pattern
    result = app.regex_search(r".*meeting.*")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test character class
    result = app.regex_search(r"[Cc]all")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test word boundary
    result = app.regex_search(r"\bme\b")
    assert len(result) == 1
    assert result[0] == conv_key


def test_regex_search_participant_ids():
    """Test regex search in participant IDs."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["user123", "admin456", "guest789"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversations with different participants
    conv_key1 = app.create_group_conversation(
        user_ids=app.get_user_ids(["user123", "admin456"]),
        title="Admin Chat",
    )

    conv_key2 = app.create_group_conversation(
        user_ids=app.get_user_ids(["guest789", "admin456"]),
        title="Guest Chat",
    )

    # Get the actual participant IDs (UUIDs) to test with
    user123_id = app.get_user_id("user123")
    admin456_id = app.get_user_id("admin456")
    guest789_id = app.get_user_id("guest789")

    # Test matching participant with regex using actual UUID patterns
    # Since UUIDs are hex strings, we can search for parts of them
    result = app.regex_search(user123_id[:8])  # Search for first 8 chars of UUID
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test matching admin in both conversations
    result = app.regex_search(admin456_id[:8])
    assert len(result) == 2
    assert conv_key1 in result
    assert conv_key2 in result

    # Test matching guest
    result = app.regex_search(guest789_id[:8])
    assert len(result) == 1
    assert result[0] == conv_key2

    # Test hex pattern that should match UUIDs
    result = app.regex_search(r"[a-f0-9]{8}")
    assert len(result) == 2
    assert conv_key1 in result
    assert conv_key2 in result


def test_regex_search_conversation_titles():
    """Test regex search in conversation titles."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversations with different titles
    conv_key1 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Project Alpha Discussion",
    )

    conv_key2 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Charlie", "Bob"]),
        title="Beta Testing Group",
    )

    conv_key3 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Charlie"]),
        title="Weekend Plans",
    )

    # Test exact title match
    result = app.regex_search("Project Alpha Discussion")
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test partial title match
    result = app.regex_search("Alpha")
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test case insensitive title match
    result = app.regex_search("BETA")
    assert len(result) == 1
    assert result[0] == conv_key2

    # Test regex pattern in title
    result = app.regex_search(r".*Testing.*")
    assert len(result) == 1
    assert result[0] == conv_key2

    # Test pattern matching multiple titles
    result = app.regex_search(r"\b[A-Z]\w+\b")  # Words starting with capital letter
    assert len(result) == 3
    assert conv_key1 in result
    assert conv_key2 in result
    assert conv_key3 in result


def test_regex_search_with_date_filters():
    """Test regex search with date filtering."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversation with messages at different times
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Test Conversation",
    )

    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Good morning everyone!",
        get_timestamp("2023-01-01 9:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Bob"),
        "Good afternoon team!",
        get_timestamp("2023-01-01 14:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Good evening folks!",
        get_timestamp("2023-01-01 19:00:00"),
    )

    # Test search with min_date filter
    result = app.regex_search(query="Good", min_date="2023-01-01 12:00:00")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test search with max_date filter
    result = app.regex_search(query="Good", max_date="2023-01-01 12:00:00")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test search with both date filters
    result = app.regex_search(
        query="Good", min_date="2023-01-01 13:00:00", max_date="2023-01-01 15:00:00"
    )
    assert len(result) == 1
    assert result[0] == conv_key

    # Test search with date range that excludes all messages
    result = app.regex_search(
        query="Good", min_date="2023-01-02 00:00:00", max_date="2023-01-02 23:59:59"
    )
    assert len(result) == 0

    # Test search without date filter should find all
    result = app.regex_search("Good")
    assert len(result) == 1
    assert result[0] == conv_key


def test_regex_search_multiple_conversations():
    """Test regex search across multiple conversations."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie", "Dave"])
    environment = Environment()
    environment.register_apps([app])

    # Create multiple conversations
    conv_key1 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Work Discussion",
    )
    app.add_message(
        conv_key1,
        app.get_user_id("Alice"),
        "Let's discuss the project timeline",
        get_timestamp("2023-01-01 10:00:00"),
    )

    conv_key2 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Charlie", "Dave"]),
        title="Personal Chat",
    )
    app.add_message(
        conv_key2,
        app.get_user_id("Charlie"),
        "How's your project going?",
        get_timestamp("2023-01-01 11:00:00"),
    )

    conv_key3 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Charlie"]),
        title="Random Stuff",
    )
    app.add_message(
        conv_key3,
        app.get_user_id("Alice"),
        "Did you see the news today?",
        get_timestamp("2023-01-01 12:00:00"),
    )

    # Test pattern that matches multiple conversations
    result = app.regex_search("project")
    assert len(result) == 2
    assert conv_key1 in result
    assert conv_key2 in result

    # Test pattern that matches only one conversation
    result = app.regex_search("timeline")
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test pattern that matches conversation title
    result = app.regex_search("Work")
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test pattern that matches no conversations
    result = app.regex_search("nonexistent")
    assert len(result) == 0


def test_regex_search_invalid_regex():
    """Test regex search with invalid regex patterns."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Test Conversation",
    )
    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Hello world!",
        get_timestamp("2023-01-01 10:00:00"),
    )

    # Test invalid regex patterns that should raise exceptions
    with pytest.raises(re.error):
        app.regex_search("[invalid")

    with pytest.raises(re.error):
        app.regex_search("*invalid")

    with pytest.raises(re.error):
        app.regex_search("(?P<invalid")


def test_regex_search_empty_query():
    """Test regex search with empty query."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create a conversation
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Test Conversation",
    )
    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Hello world!",
        get_timestamp("2023-01-01 10:00:00"),
    )

    # Test empty query - should match everything
    result = app.regex_search("")
    assert len(result) == 1
    assert result[0] == conv_key


def test_regex_search_no_conversations():
    """Test regex search when no conversations exist."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Test search with no conversations
    result = app.regex_search("anything")
    assert len(result) == 0


def test_regex_search_special_characters():
    """Test regex search with special characters and escape sequences."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversation with special characters
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Special Characters: $100 & More!",
    )

    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Price is $50.99 (including tax)",
        get_timestamp("2023-01-01 10:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Bob"),
        "Email me at user@domain.com",
        get_timestamp("2023-01-01 11:00:00"),
    )

    # Test literal dollar sign
    result = app.regex_search(r"\$")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test literal parentheses
    result = app.regex_search(r"\(.*\)")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test literal dot in email
    result = app.regex_search(r"\.com")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test ampersand in title
    result = app.regex_search("&")
    assert len(result) == 1
    assert result[0] == conv_key


def test_regex_search_unicode_and_emojis():
    """Test regex search with Unicode characters and emojis."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversation with Unicode and emojis
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Fun Chat 🎉",
    )

    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Hello! 👋 How are you? 😊",
        get_timestamp("2023-01-01 10:00:00"),
    )
    app.add_message(
        conv_key,
        app.get_user_id("Bob"),
        "Café is great ☕",
        get_timestamp("2023-01-01 11:00:00"),
    )

    # Test emoji search in title
    result = app.regex_search("🎉")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test emoji search in message
    result = app.regex_search("👋")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test Unicode character
    result = app.regex_search("Café")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test case insensitive Unicode
    result = app.regex_search("CAFÉ")
    assert len(result) == 1
    assert result[0] == conv_key


def test_regex_search_complex_scenarios():
    """Test regex search with complex real-world scenarios."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob", "Charlie"])
    environment = Environment()
    environment.register_apps([app])

    # Create multiple conversations with various content
    conv_key1 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="Project Alpha - Phase 1",
    )
    app.add_message(
        conv_key1,
        app.get_user_id("Alice"),
        "Meeting scheduled for 2023-12-15 at 2:30 PM",
        get_timestamp("2023-01-01 10:00:00"),
    )
    app.add_message(
        conv_key1,
        app.get_user_id("Bob"),
        "Budget: $15,000 - $20,000",
        get_timestamp("2023-01-01 11:00:00"),
    )

    conv_key2 = app.create_group_conversation(
        user_ids=app.get_user_ids(["Charlie", "Bob"]),
        title="Beta Testing Results",
    )
    app.add_message(
        conv_key2,
        app.get_user_id("Charlie"),
        "Test case TC-001 passed, TC-002 failed",
        get_timestamp("2023-01-01 12:00:00"),
    )

    # Test date pattern matching
    result = app.regex_search(r"\d{4}-\d{2}-\d{2}")
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test currency pattern matching
    result = app.regex_search(r"\$[\d,]+")
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test test case ID pattern
    result = app.regex_search(r"TC-\d{3}")
    assert len(result) == 1
    assert result[0] == conv_key2

    # Test project phase pattern
    result = app.regex_search(r"Phase \d+")
    assert len(result) == 1
    assert result[0] == conv_key1

    # Test alternation pattern
    result = app.regex_search(r"Alpha|Beta")
    assert len(result) == 2
    assert conv_key1 in result
    assert conv_key2 in result


def test_regex_search_edge_cases():
    """Test regex search edge cases."""
    app = MessagingAppV2(current_user_id="42", current_user_name="Me")
    app.add_users(["Alice", "Bob"])
    environment = Environment()
    environment.register_apps([app])

    # Create conversation with edge case content
    conv_key = app.create_group_conversation(
        user_ids=app.get_user_ids(["Alice", "Bob"]),
        title="",  # Empty title
    )

    # Add message with only whitespace
    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "   ",
        get_timestamp("2023-01-01 10:00:00"),
    )

    # Add empty message
    app.add_message(
        conv_key,
        app.get_user_id("Bob"),
        "",
        get_timestamp("2023-01-01 11:00:00"),
    )

    # Add normal message
    app.add_message(
        conv_key,
        app.get_user_id("Alice"),
        "Normal message",
        get_timestamp("2023-01-01 12:00:00"),
    )

    # Test whitespace pattern
    result = app.regex_search(r"^\s+$")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test empty string pattern
    result = app.regex_search(r"^$")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test normal content
    result = app.regex_search("Normal")
    assert len(result) == 1
    assert result[0] == conv_key

    # Test pattern that matches participant ID (should work even with empty title)
    alice_id = app.get_user_id("Alice")
    result = app.regex_search(alice_id[:8])  # Search for first 8 chars of Alice's UUID
    assert len(result) == 1
    assert result[0] == conv_key
