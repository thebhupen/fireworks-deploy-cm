# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import base64
import os
import re
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import partial
from typing import Any, Callable

from rapidfuzz import process

from are.simulation.apps.app import App, Protocol, ToolType
from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.apps.virtual_file_system import VirtualFileSystem
from are.simulation.tool_utils import (
    AppTool,
    OperationType,
    ToolAttributeName,
    app_tool,
    env_tool,
)
from are.simulation.types import EventType, disable_events, event_registered
from are.simulation.utils import get_state_dict, type_check, uuid_hex


@dataclass
class MessageV2:
    sender_id: str
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=lambda: time.time())
    content: str = ""

    def __str__(self):
        return textwrap.dedent(
            f"""
        Sender Id: {self.sender_id}
        message_id: {self.message_id}
        timestamp: {str(self.timestamp)}
        content: {self.content}
        """
        )

    def __post_init__(self):
        if self.message_id is None or len(self.message_id) == 0:
            self.message_id = uuid.uuid4().hex


@dataclass
class FileMessageV2(MessageV2):
    attachment: bytes | None = None
    attachment_name: str | None = None

    def __str__(self):
        if self.attachment_name is None:
            self.attachment_name = ""
        return textwrap.dedent(
            f"""
        sender_id: {self.sender_id}
        message_id: {self.message_id}
        timestamp: {str(self.timestamp)}
        content: {self.content}
        attachment_name: {self.attachment_name}
        """
        )


@dataclass
class ConversationV2:
    participant_ids: list[str]
    messages: list[MessageV2] = field(default_factory=list)
    title: str | None = field(default=None)
    conversation_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    last_updated: float = field(default_factory=lambda: time.time())

    def __post_init__(self):
        if self.title is None or self.title == "":
            self.title = ", ".join(self.participant_ids)
        self.participant_ids = list(set(self.participant_ids))
        if self.conversation_id is None or len(self.conversation_id) == 0:
            self.conversation_id = uuid.uuid4().hex

    @property
    def summary(self):
        return f"{self.title}: {self.conversation_id} (last updated: {datetime.fromtimestamp(self.last_updated, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')})"

    def update_last_updated(self, timestamp: float):
        self.last_updated = max(timestamp, self.last_updated)

    def __str__(self):
        participants_str = ", ".join(sorted(list(self.participant_ids)))
        messages_str = "\n".join([str(msg) for msg in self.messages])

        return textwrap.dedent(
            f"""
        participants: {participants_str}
        messages: {messages_str}
        title: {self.title}
        conversation_id: {self.conversation_id}
        last_updated: {str(self.last_updated)}
        """
        )

    def load_state(self, state_dict: dict[str, Any]):
        self.participant_ids = state_dict["participant_ids"]
        self.title = state_dict["title"]
        self.conversation_id = state_dict["conversation_id"]
        self.last_updated = state_dict["last_updated"]
        for message in state_dict["messages"]:
            if "attachment" in message:
                self.messages.append(FileMessageV2(**message))
            else:
                self.messages.append(MessageV2(**message))

    def get_messages_in_date_range(
        self, start_date: str | None, end_date: str | None
    ) -> list[MessageV2]:
        start_timestamp = -float("inf")
        end_timestamp = float("inf")
        if start_date is not None:
            start_timestamp = (
                datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        if end_date is not None:
            end_timestamp = (
                datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        return [
            msg
            for msg in self.messages
            if start_timestamp <= int(msg.timestamp) <= end_timestamp
        ]


class MessagingAppMode(Enum):
    """
    Enum for MessagingApp modes
    """

    NAME = "NAME"
    PHONE_NUMBER = "PHONE_NUMBER"


# This is almost a copy of MessagingApp, but with a few changes:
# - Users are handled through Ids instead of names
# - There are 2 modes: NAME assigns Ids to names, PHONE_NUMBER uses phone numbers as Ids and allows to send to any number
# - send_message first checks that a conversation exists, if not it creates one
@dataclass
class MessagingAppV2(App):
    """
    A messaging application that provides comprehensive functionality for managing conversations,
    messages, and file attachments. This class implements a chat system with support for
    individual and group conversations, message history, and file sharing capabilities.

    The MessagingApp maintains conversations as a dictionary of Conversation objects, where each
    conversation has unique identifiers, participants, messages, and metadata. The system supports
    both text messages and file attachments with configurable view limits.

    Key Features:
    - Conversation Management: Create, list, and search conversations
    - Messaging: Send text messages and file attachments
    - Participant Management: Add/remove participants to conversations
    - File Handling: Send and download file attachments
    - Search Functionality: Search across conversations, participants, and messages
    - View Limits: Configurable limits for messages and conversation listings
    - State Management: Save and load application state

    Conversation Features:
    - Unique conversation IDs
    - Optional conversation titles
    - Participant management
    - Message history with timestamps
    - Last updated tracking
    - File attachment support

    Notes:
    - The current user is automatically added as "Me" to all conversations
    - Messages are sorted by timestamp, most recent first
    - File attachments are handled using base64 encoding
    - Search operations are case-insensitive
    - Conversations maintain participant lists and message history
    - All operations are tracked through event registration
    - Messages can be paginated using offset and limit parameters
    """

    current_user_id: str | None = None
    current_user_name: str | None = None
    name: str | None = None
    mode: MessagingAppMode = MessagingAppMode.NAME
    id_to_name: dict[str, str] = field(default_factory=dict)
    name_to_id: dict[str, str] = field(default_factory=dict)
    conversations: dict[str, ConversationV2] = field(default_factory=dict)
    # View limit of messages in a conversation
    messages_view_limit: int = 10
    # View limit of conversations when listing conversations
    conversation_view_limit: int = 5
    internal_fs: SandboxLocalFileSystem | VirtualFileSystem | None = None

    def __post_init__(self):
        super().__init__(self.name)
        if len(self.name_to_id) == 0 and len(self.id_to_name) > 0:
            self.name_to_id = {v: k for k, v in self.id_to_name.items()}
        elif len(self.name_to_id) > 0 and len(self.id_to_name) == 0:
            self.id_to_name = {v: k for k, v in self.name_to_id.items()}
        if self.current_user_id is not None and self.current_user_name is not None:
            self.id_to_name[self.current_user_id] = self.current_user_name
            self.name_to_id[self.current_user_name] = self.current_user_id

    def connect_to_protocols(self, protocols: dict[Protocol, Any]) -> None:
        file_system = protocols.get(Protocol.FILE_SYSTEM)
        if isinstance(file_system, (SandboxLocalFileSystem, VirtualFileSystem)):
            self.internal_fs = file_system

    def get_state(self) -> dict[str, Any]:
        return get_state_dict(
            self,
            [
                "conversations",
                "messages_view_limit",
                "conversation_view_limit",
                "mode",
                "name_to_id",
                "id_to_name",
                "current_user_id",
                "current_user_name",
            ],
        )

    def load_state(self, state_dict: dict[str, Any]):
        self.load_conversations_from_dict(state_dict["conversations"])
        self.messages_view_limit = state_dict["messages_view_limit"]
        self.conversation_view_limit = state_dict["conversation_view_limit"]
        self.mode = MessagingAppMode(state_dict["mode"])
        self.name_to_id = state_dict["name_to_id"]
        self.id_to_name = state_dict["id_to_name"]
        self.current_user_id = state_dict["current_user_id"]
        self.current_user_name = state_dict["current_user_name"]

    def load_conversations_from_dict(self, conversations_dict):
        for conversation_id in conversations_dict:
            conversation = ConversationV2(
                conversation_id=conversation_id,
                title=conversations_dict[conversation_id]["title"],
                participant_ids=conversations_dict[conversation_id]["participant_ids"],
            )
            conversation.load_state(conversations_dict[conversation_id])
            self.conversations[conversation_id] = conversation

    def reset(self):
        super().reset()
        self.conversations = {}

    def add_users(self, user_names: list[str]):
        for user_name in user_names:
            if user_name not in self.name_to_id:
                user_id = uuid_hex(self.rng)
                self.name_to_id[user_name] = user_id
                self.id_to_name[user_id] = user_name

    def add_contacts(self, contacts: list[tuple[str, str]]):
        for user_name, phone in contacts:
            if user_name not in self.name_to_id:
                self.name_to_id[user_name] = phone
                self.id_to_name[phone] = user_name

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_user_id(self, user_name: str) -> str | None:
        """
        Get the user id for a given user name, the name must match EXACTLY, otherwise this returns None.
        :param user_name: user name
        :returns: user id
        """
        return self.name_to_id.get(user_name, None)

    def get_user_ids(self, user_names: list[str]) -> list[str | None]:
        return [self.name_to_id.get(user_name, None) for user_name in user_names]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_user_name_from_id(self, user_id: str) -> str | None:
        """
        Get the user name for a given user id, the id must match EXACTLY, otherwise returns None.
        :param user_id: user id
        :returns: user name
        """
        return self.id_to_name.get(user_id, None)

    def get_user_names(self, user_ids: list[str]) -> list[str | None]:
        return [self.id_to_name.get(user_id, None) for user_id in user_ids]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def lookup_user_id(self, user_name: str) -> dict[str, str]:
        """
        Lookup the user id for a given user name, this is an fuzzy string based search so what is returned might not be exactly the query
        returns Dictionary of user name to user id, for people names that are close enough to the query user_name.
        dictionary will be empty if no matches are found
        :param user_name: user name to lookup
        :returns: Dictionary of user name to user id, for people names that are close enough to the query user_name
        """
        threshold = 80
        if user_name in self.name_to_id:
            return {user_name: self.name_to_id[user_name]}
        else:
            query = user_name.lower().strip()
            matches = process.extract(
                query,
                choices=self.name_to_id.keys(),
                processor=str.lower,
                limit=None,
                score_cutoff=threshold,
            )

            return {name: self.name_to_id[name] for name, _, _ in matches}

    @event_registered(operation_type=OperationType.WRITE)
    def add_conversation(self, conversation: ConversationV2) -> None:
        """
        Add a conversation to the app.
        :param conversation: The conversation to add.
        """
        assert isinstance(conversation, ConversationV2), (
            "Conversation must be an instance of Conversation."
        )
        self.conversations[conversation.conversation_id] = conversation

    def add_conversations(self, conversations: list[ConversationV2]) -> None:
        """
        Add a list of conversations to the app.
        :param conversations: The conversations to add.
        """
        assert all(isinstance(conv, ConversationV2) for conv in conversations), (
            "All conversations must be an instance of Conversation."
        )
        for conv in conversations:
            self.add_conversation(conv)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def send_message(
        self,
        user_id: str,
        content: str = "",
        attachment_path: str | None = None,
        # ) -> dict[str, str]:
    ) -> str:
        """
        Send a message to the specified recipient, if an existing conversation with the same recipient exists,
        the message will be added to that conversation, otherwise a new conversation will be created.
        This is the only way to send a message to a single person.

        :param user_id: The recipient id to send the message to
        :param content: The message content.
        :param attachment_path: Optional path to an attachment file to send with the message.
        :returns: a str, "conversation_id": Id of the conversation the message was sent to
        """

        # :returns: dict containing 2 keys "message_id": Id of the sent message, "conversation_id": Id of the conversation the message was sent to

        assert self.current_user_id is not None, "Current user id must be set"
        message = self._create_message(self.current_user_id, content, attachment_path)
        conversation_id = self._get_or_create_default_conversation([user_id])

        self.conversations[conversation_id].messages.append(message)
        self.conversations[conversation_id].update_last_updated(message.timestamp)
        # return {
        #     "message_id": message.message_id,
        #     "conversation_id": conversation_id,
        # }

        return conversation_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def send_message_to_group_conversation(
        self,
        conversation_id: str,
        content: str = "",
        attachment_path: str | None = None,
        # ) -> dict[str, str]:
    ) -> str:
        """
        Send a message to an existing group conversation.

        :param conversation_id: The conversation id to send the message to
        :param content: The message content.
        :param attachment_path: Optional path to an attachment file to send with the message.
        :returns: a str, "conversation_id": Id of the conversation the message was sent to
        """

        # :returns: dict containing 2 keys "message_id": Id of the sent message, "conversation_id": Id of the conversation the message was sent to

        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} does not exist")
        if len(self.conversations[conversation_id].participant_ids) < 3:
            raise ValueError(
                f"Conversation {conversation_id} is not a group conversation"
            )
        assert self.current_user_id is not None, "Current user id must be set"
        message = self._create_message(self.current_user_id, content, attachment_path)

        self.conversations[conversation_id].messages.append(message)
        self.conversations[conversation_id].update_last_updated(message.timestamp)
        # return {
        #     "message_id": message.message_id,
        #     "conversation_id": conversation_id,
        # }
        return conversation_id

    def _create_message(
        self, sender_id: str, content: str, attachment_path: str | None
    ) -> MessageV2:
        assert self.current_user_id is not None, "Current user id must be set"
        timestamp = self.time_manager.time()
        if attachment_path is None:
            message = MessageV2(
                message_id=uuid_hex(self.rng),
                sender_id=self.current_user_id,
                content=content,
                timestamp=timestamp,
            )
        elif os.path.exists(attachment_path) or (
            self.internal_fs is not None and self.internal_fs.exists(attachment_path)
        ):
            if self.internal_fs is not None:
                with disable_events():
                    with self.internal_fs.open(attachment_path, "rb") as f:
                        file_content = base64.b64encode(f.read())
            else:
                with open(attachment_path, "rb") as f:
                    file_content = base64.b64encode(f.read())
            file_name = os.path.basename(attachment_path)
            message = FileMessageV2(
                sender_id=sender_id,
                content=content,
                timestamp=timestamp,
                attachment=file_content,
                attachment_name=file_name,
            )
        else:
            raise ValueError(f"File {attachment_path} does not exist")
        return message

    def _get_or_create_default_conversation(self, user_ids: list[str]) -> str:
        """
        Ensure a conversation exists for the recipients, one that has no specific title. If not, create one.
        :param recipient: The recipient's user ID or phone number.
        :returns: The conversation ID.
        """
        conv_ids = self.get_existing_conversation_ids(user_ids)
        default_title = self.get_default_title(user_ids)

        # If we already have an untitled conversation with exactly the same participants, use that.
        conversation_with_default_title = [
            conversation_id
            for conversation_id in conv_ids
            if self.conversations[conversation_id].title == default_title
        ]

        if len(conversation_with_default_title) > 0:
            return conversation_with_default_title[0]

        # Create a new conversation if none exists.
        participants = [self.current_user_id] + user_ids
        conversation_id = self._create_conversation(participants)  # type: ignore
        return conversation_id

    @type_check
    @app_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def create_group_conversation(
        self, user_ids: list[str], title: str | None = None
    ) -> str:
        """
        Create a new group conversation with the given participants.
        There must be at least two participants participants other than the current user.
        If title is not provided, it will be set to the participant names.
        :param user_ids: List of Ids of the participants in the conversation. The current user is automatically added.
        :param title: Optional title for the conversation
        :returns: Id of the created conversation
        """
        if len(user_ids) < 2:
            raise Exception("Must have at least two other participants")
        return self._create_conversation(user_ids, title)

    def _create_conversation(
        self, user_ids: list[str], title: str | None = None
    ) -> str:
        """
        Create a new conversation with the given participants.
        If title is not provided, it will be set to the participant names.
        :param user_ids: List of Ids of the participants in the conversation. The current user is automatically added.
        :param title: Optional title for the conversation
        :returns: Id of the created conversation
        """
        if len(user_ids) < 1:
            raise Exception("Must have at least one participant")
        for user_id in user_ids:
            if self.mode == MessagingAppMode.NAME:
                # In this mode, we can only send messages to people that are in the Ids
                if user_id not in self.id_to_name:
                    raise ValueError(
                        f"User {user_id} does not exist in Ids, you need to provide the Id of an existing user"
                    )
            elif self.mode == MessagingAppMode.PHONE_NUMBER:
                # In this mode, we can send to any phone number
                if all(not c.isdigit() for c in user_id):
                    raise ValueError(
                        f"User {user_id} is not a valid phone number, you need to provide the phone number of an existing user"
                    )
            else:
                raise ValueError(f"Unknown mode: {self.mode}")

        title = self.get_default_title(user_ids) if title is None else title

        user_ids_set = set(user_ids)
        user_ids_set.add(self.current_user_id)  # type: ignore

        conversation = ConversationV2(
            conversation_id=uuid_hex(self.rng),
            participant_ids=list(user_ids_set),
            title=title,
        )
        self.conversations[conversation.conversation_id] = conversation
        return conversation.conversation_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_existing_conversation_ids(self, user_ids: list[str]) -> list[str]:
        """
        Get the list of conversation ids for the given participants.
        :param user_ids: List of Ids of the participants in the conversation. The current user is automatically added.
        :returns: List of Ids of the conversations
        """
        user_ids_set = set(user_ids)
        user_ids_set.add(self.current_user_id)  # type: ignore
        ids = []
        for conv_id, conversation in self.conversations.items():
            if user_ids_set == set(conversation.participant_ids):
                ids.append(conv_id)
        return ids

    def apply_conversation_limits(
        self,
        conversations: list[ConversationV2],
        offset_recent_messages_per_conversation: int,
        limit_recent_messages_per_conversation: int,
    ) -> list[ConversationV2]:
        if limit_recent_messages_per_conversation > self.messages_view_limit:
            raise ValueError(
                f"Limit must be smaller than the view limit of {self.messages_view_limit} - Please use a smaller limit and use offset to navigate"
            )

        if offset_recent_messages_per_conversation < 0:
            raise ValueError("Offset must be non-negative")

        new_conversations = []
        for conversation in conversations:
            start_index = offset_recent_messages_per_conversation
            sorted_messages = sorted(
                conversation.messages, key=lambda msg: msg.timestamp, reverse=True
            )
            end_index = min(
                len(conversation.messages),
                offset_recent_messages_per_conversation
                + limit_recent_messages_per_conversation,
            )
            new_conversation = ConversationV2(
                participant_ids=conversation.participant_ids,
                messages=sorted_messages[start_index:end_index],
                title=conversation.title,
                conversation_id=conversation.conversation_id,
                last_updated=conversation.last_updated,
            )
            new_conversations.append(new_conversation)
        return new_conversations

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_recent_conversations(
        self,
        offset: int = 0,
        limit: int = 5,
        offset_recent_messages_per_conversation: int = 0,
        limit_recent_messages_per_conversation: int = 10,
    ) -> list[ConversationV2]:
        """
        List conversations ordered by the most recent modification, considering an offset and view limit.
        e.g. list_recent_conversations(0, 5) will list the 5 most recent conversations.
        :param offset: The starting index from which to list conversations
        :param limit: The number of conversations to list, this number needs to be small otherwise an error will be raised
        :param offset_recent_messages_per_conversation: The starting index from which to list messages per conversation
        :param limit_recent_messages_per_conversation: The number of messages to list per conversation, this number needs to be small otherwise an error will be raised
        :returns: List of Conversation details

        :example:
            list_recent_conversations(0, 5)
        """
        if limit > self.conversation_view_limit:
            raise ValueError(
                f"Limit must be smaller than the view limit of {self.conversation_view_limit} - Please use a smaller limit and use offset to navigate"
            )
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        if offset > len(self.conversations):
            raise ValueError("Offset is larger than the number of conversations")

        sorted_conversations = sorted(
            self.conversations.values(),
            key=lambda conv: conv.last_updated,
            reverse=True,
        )

        # Calculate the start and end indices based on the offset and view limit
        start_index = offset
        end_index = offset + limit

        # Ensure the end index does not exceed the list size
        end_index = min(end_index, len(sorted_conversations))

        return self.apply_conversation_limits(
            sorted_conversations[start_index:end_index],
            offset_recent_messages_per_conversation,
            limit_recent_messages_per_conversation,
        )

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_conversations_by_participant(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 5,
        offset_recent_messages_per_conversation: int = 0,
        limit_recent_messages_per_conversation: int = 5,
    ) -> list[ConversationV2]:
        """
        List all the conversations with the given participant.
        :param user_id: User Id of the participant in the conversation
        :param offset: The starting index from which to list conversations
        :param limit: The number of conversations to list, this number needs to be small otherwise an error will be raised
        :param offset_recent_messages_per_conversation: The starting index from which to list messages per conversation
        :param limit_recent_messages_per_conversation: The number of messages to list per conversation, this number needs to be small otherwise an error will be raised
        :returns: List of Conversation details

        :example:
            list_conversations_by_participant("1234-abcde", 0, 5)
        """

        if limit > self.conversation_view_limit:
            raise ValueError(
                f"Limit must be smaller than the view limit of {self.conversation_view_limit} - Please use a smaller limit and use offset to navigate"
            )
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        if offset > len(self.conversations):
            raise ValueError("Offset is larger than the number of conversations")

        conversations = [
            conv
            for conv_id, conv in self.conversations.items()
            if any(user_id in p_fullname for p_fullname in conv.participant_ids)
        ]

        # Calculate the start and end indices based on the offset and view limit
        start_index = offset
        end_index = offset + limit

        # Ensure the end index does not exceed the list size
        end_index = min(end_index, len(conversations))
        return self.apply_conversation_limits(
            conversations[start_index:end_index],
            offset_recent_messages_per_conversation,
            limit_recent_messages_per_conversation,
        )

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def download_attachment(
        self, conversation_id: str, message_id: str, download_path: str = "Downloads/"
    ) -> str:
        """
        Download an attachment from the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param message_id: Message id
        :param download_path: Path to download the attachment to
        :returns: Full path to the downloaded attachment if successful, otherwise raise Exception

        :example:
            download_attachment("1234567890abcdef", "abcdef1234567890", "Downloads/")
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")

        conversation = self.conversations[conversation_id]
        message = next(
            (msg for msg in conversation.messages if msg.message_id == message_id),
            None,  # type: ignore
        )

        if not message or not message.attachment:  # type: ignore
            raise Exception("No attachment found in the specified message")

        file_data = base64.b64decode(message.attachment)  # type: ignore
        full_path = os.path.join(download_path, message.attachment_name)  # type: ignore

        if self.internal_fs is not None:
            with disable_events():
                with self.internal_fs.open(full_path, "wb") as file:
                    file.write(file_data)
        else:
            with open(full_path, "wb") as file:
                file.write(file_data)

        return full_path

    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
        timestamp: float | None = None,
    ) -> None:
        """
        Send a message to the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param sender_id: Sender id
        :param content: Message content
        :param timestamp: Timestamp of the message, if not provided, will be set to current time
        :returns: None
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if sender_id not in self.conversations[conversation_id].participant_ids:
            raise Exception(f"Sender {sender_id} not in conversation")
        timestamp = timestamp if timestamp else self.time_manager.time()
        self.conversations[conversation_id].messages.append(  # type: ignore
            MessageV2(
                message_id=uuid_hex(self.rng),
                sender_id=sender_id,
                content=content,
                timestamp=timestamp,
            )
        )
        self.conversations[conversation_id].update_last_updated(timestamp)

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def create_and_add_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
    ) -> None:
        """
        Send a message to the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param sender_id: Sender id
        :param content: Message content
        :returns: None
        """
        message_time: str = datetime.fromtimestamp(
            self.time_manager.time(), tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
        timestamp = (
            datetime.strptime(message_time, "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if sender_id not in self.conversations[conversation_id].participant_ids:
            raise Exception(f"Sender {sender_id} not in conversation")
        self.conversations[conversation_id].messages.append(  # type: ignore
            MessageV2(
                message_id=uuid_hex(self.rng),
                sender_id=sender_id,
                content=content,
                timestamp=timestamp,
            )
        )
        self.conversations[conversation_id].update_last_updated(timestamp)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def read_conversation(
        self,
        conversation_id: str,
        offset: int = 0,
        limit: int = 10,
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> dict:
        """
        Read the conversation with the given conversation_id.
        Shows the last 'limit' messages after offset. Which means messages between offset and offset + limit will be shown.
        Messages are sorted by timestamp, most recent first.
        :param conversation_id: Conversation id
        :param offset: Offset to shift the view window
        :param limit: Number of messages to show
        :param min_date: Minimum date of the messages to be shown (YYYY-MM-DD %H:%M:%S format). Default is None, which means no minimum date.
        :param max_date: Maximum date of the messages to be shown (YYYY-MM-DD %H:%M:%S format). Default is None, which means no maximum date.
        :returns: Dict with messages and additional info

        :example:
            read_conversation("1234567890abcdef", 0, 10)
        """

        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found")
        if offset < 0:
            raise ValueError("Offset must be positive")

        conversation = self.conversations[conversation_id]
        messages = conversation.get_messages_in_date_range(min_date, max_date)
        if offset > len(messages):  # type: ignore
            raise ValueError("Offset is larger than the number of messages")
        messages.sort(key=lambda x: x.timestamp, reverse=True)
        conversation_length = len(messages)  # type: ignore

        start_index = offset
        end_index = min(len(messages), offset + limit)  # type: ignore

        messages = messages[start_index:end_index]  # type: ignore
        return {
            "messages": [
                message
                for message in messages
                if isinstance(message, MessageV2)  # TODO: handle attachments
            ],
            "metadata": {
                "message_range": (start_index, end_index),
                "conversation_length": conversation_length,  # type: ignore
                "conversation_id": conversation_id,
                "conversation_title": conversation.title,
            },
        }

    @type_check
    @app_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_participant_to_conversation(
        self, conversation_id: str, user_id: str
    ) -> str:
        """
        Add a user to the conversation with the given conversation_id and updates the title if title is list of participants.
        :param conversation_id: Conversation id to be updated
        :param user_id: Id of the Participant to be added
        :returns: conversation_id of the conversation just updated, if successful, otherwise raise Exception.
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if user_id in self.conversations[conversation_id].participant_ids:
            raise Exception(f"Participant {user_id} already in conversation")

        update_title = self.conversations[
            conversation_id
        ].title == self.get_default_title(
            self.conversations[conversation_id].participant_ids
        )

        self.conversations[conversation_id].participant_ids.append(user_id)

        if update_title:
            self.conversations[conversation_id].title = self.get_default_title(
                self.conversations[conversation_id].participant_ids
            )

        return conversation_id

    @type_check
    @app_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_participant_from_conversation(
        self, conversation_id: str, user_id: str
    ) -> str:
        """
        Remove a participant from the conversation with the given conversation_id and updates the title if title is list of participants.
        :param conversation_id: Conversation id
        :param user_id: Id of the Participant to be removed
        :returns: conversation_id of the conversation just updated, if successful, otherwise raise Exception.
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if user_id not in self.conversations[conversation_id].participant_ids:
            raise Exception(f"Participant {user_id} not in conversation")

        update_title = self.conversations[
            conversation_id
        ].title == self.get_default_title(
            self.conversations[conversation_id].participant_ids
        )

        self.conversations[conversation_id].participant_ids.remove(user_id)

        if update_title:
            self.conversations[conversation_id].title = self.get_default_title(
                self.conversations[conversation_id].participant_ids
            )

        return conversation_id

    @type_check
    @app_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def change_conversation_title(self, conversation_id: str, title: str) -> str:
        """
        Change the title of the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param title: New title for the conversation
        :returns: conversation_id of the conversation just updated, if successful, otherwise raise Exception.

        :example:
            change_conversation_title("1234567890abcdef", "My new title")
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")

        self.conversations[conversation_id].title = title
        return conversation_id

    def get_all_conversations(self) -> list[ConversationV2]:
        """
        Get all conversations.
        :returns: List of Conversation objects
        """
        sorted_conversations = sorted(self.conversations.items())
        return [conv for _, conv in sorted_conversations]

    def get_default_title(self, user_ids: list[str]) -> str:
        """
        Get the default title for a conversation with the given participants.
        :param user_ids: List of Ids of the participants in the conversation, these are the names of the contacts, current user is automatically added
        :returns: Default title for the conversation
        """
        user_ids_set = set(user_ids)
        if self.current_user_id in user_ids_set:
            user_ids_set.remove(self.current_user_id)  # type: ignore

        participant_names = []
        for user_id in user_ids_set:
            if user_id in self.id_to_name:
                participant_names.append(self.id_to_name[user_id])
            elif self.mode == MessagingAppMode.PHONE_NUMBER:
                # We can send to any phone number
                participant_names.append(user_id)

        assert self.current_user_id in self.id_to_name  # type: ignore
        participant_names = sorted(participant_names)
        title = ", ".join(participant_names)
        return title

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search(
        self,
        query: str,
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> list[str]:
        """
        Search for conversations that match the given query.
        The search is performed on conversation participants, titles, and message content.
        Returns the Ids of the matching conversations.
        :param query: The search query string
        :param min_date: Minimum date of the messages to be searched (YYYY-MM-DD %H:%M:%S format). Defaults to None (no minimum date).
        :param max_date: Maximum date of the messages to be searched (YYYY-MM-DD %H:%M:%S format). Defaults to None (no maximum date).
        :returns: List of matching Conversation Ids

        :example:
            search("Taylor Swift")
        """
        results = []
        query = query.lower()

        for conversation in self.conversations.values():
            if self._conversation_matches(conversation, query, min_date, max_date):
                results.append(conversation.conversation_id)

        return results

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def regex_search(
        self,
        query: str,
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> list[str]:
        """
        Search for conversations that match the given regex query (case insensitive).
        The search is performed on conversation participants, titles, and message content.
        Returns the Ids of the matching conversations.
        :param query: The search query string
        :param min_date: Minimum date of the messages to be searched (YYYY-MM-DD %H:%M:%S format). Defaults to None (no minimum date).
        :param max_date: Maximum date of the messages to be searched (YYYY-MM-DD %H:%M:%S format). Defaults to None (no maximum date).
        :returns: List of matching Conversation Ids

        :example:
            regex_search("Taylor Swift")
        """
        results = []
        compiled_query = re.compile(
            query, re.IGNORECASE
        )  # Check if the query is a valid regex
        get_match = partial(re.search, compiled_query)  # Create a partial function
        for conversation in self.conversations.values():
            if self._regex_conversation_matches(
                conversation, get_match, min_date, max_date
            ):
                results.append(conversation.conversation_id)

        return results

    def _conversation_matches(
        self,
        conversation: ConversationV2,
        query: str,
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> bool:
        """
        Helper method to check if a conversation matches the query.
        """
        # Search in participants
        if any(
            query in participant.lower() for participant in conversation.participant_ids
        ):
            return True

        # Search in title
        if conversation.title is not None and query in conversation.title.lower():
            return True

        # Search in messages
        return any(
            isinstance(message, MessageV2) and query in message.content.lower()
            for message in conversation.get_messages_in_date_range(min_date, max_date)
        )

    def _regex_conversation_matches(
        self,
        conversation: ConversationV2,
        get_match: Callable[[str], re.Match | None],
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> bool:
        """
        Helper method to check if a conversation matches the query using regex.
        """
        if any(
            get_match(participant.lower())
            for participant in conversation.participant_ids
        ):
            return True

        # Search in title
        if conversation.title is not None and get_match(conversation.title.lower()):
            return True

            # Search in messages
        if any(
            isinstance(message, MessageV2) and get_match(message.content)
            for message in conversation.get_messages_in_date_range(min_date, max_date)
        ):
            return True
        return False

    def get_tools_with_attribute(
        self,
        attribute: ToolAttributeName,
        tool_type: ToolType,
    ) -> list[AppTool]:
        """
        Here we add to the description of every tool that the Ids are Phone numbers for MessagingAppMode.PHONE_NUMBER and User Ids for MessagingAppMode.NAME
        """
        tools = super().get_tools_with_attribute(attribute, tool_type)
        for tool in tools:
            if (
                self.mode == MessagingAppMode.PHONE_NUMBER
                and tool.function_description is not None
            ):
                tool.function_description = (
                    tool.function_description
                    + "\n\n All the User Ids for this tool (user_id, recipient_id, sender_id, ...) are Phone numbers"
                )
            elif (
                self.mode == MessagingAppMode.NAME
                and tool.function_description is not None
            ):
                tool.function_description = (
                    tool.function_description
                    + "\n\n All the User Ids for this tool (user_id, recipient_id, sender_id, ...) are User Ids that are internal, and thus names and Ids need to be matched"
                )
        return tools
