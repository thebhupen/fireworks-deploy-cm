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
from functools import partial
from typing import Any, Callable

from are.simulation.apps.app import App
from are.simulation.tool_utils import OperationType, app_tool, data_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import get_state_dict, type_check, uuid_hex


@dataclass
class Message:
    sender: str
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=lambda: time.time())
    content: str = ""

    def __str__(self):
        return textwrap.dedent(
            f"""
        Sender: {self.sender}
        message_id: {self.message_id}
        timestamp: {str(self.timestamp)}
        content: {self.content}
        """
        )

    def __post_init__(self):
        if self.message_id is None or len(self.message_id) == 0:
            self.message_id = uuid.uuid4().hex


@dataclass
class FileMessage(Message):
    attachment: bytes | None = None
    attachment_name: str | None = None

    def __str__(self):
        if self.attachment_name is None:
            self.attachment_name = ""
        return textwrap.dedent(
            f"""
        sender: {self.sender}
        message_id: {self.message_id}
        timestamp: {str(self.timestamp)}
        content: {self.content}
        attachment_name: {self.attachment_name}
        """
        )


@dataclass
class Conversation:
    participants: list[str]
    messages: list[Message] = field(default_factory=list)
    title: str | None = ""
    conversation_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    last_updated: float = field(default_factory=lambda: time.time())

    def __post_init__(self):
        if self.title is None or self.title == "":
            self.title = ", ".join(self.participants)
        self.participants = list(set(self.participants))
        if self.conversation_id is None or len(self.conversation_id) == 0:
            self.conversation_id = uuid.uuid4().hex

    @property
    def summary(self):
        return f"{self.title}: {self.conversation_id} (last updated: {datetime.fromtimestamp(self.last_updated, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')})"

    def update_last_updated(self, timestamp: float):
        self.last_updated = max(timestamp, self.last_updated)

    def __str__(self):
        participants_str = ", ".join(sorted(list(self.participants)))
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
        self.participants = state_dict["participants"]
        self.title = state_dict["title"]
        self.conversation_id = state_dict["conversation_id"]
        self.last_updated = state_dict["last_updated"]
        for message in state_dict["messages"]:
            if "attachment" in message:
                self.messages.append(FileMessage(**message))
            else:
                self.messages.append(Message(**message))

    def get_messages_in_date_range(
        self, start_date: str | None, end_date: str | None
    ) -> list[Message]:
        start_timestamp = -float("inf")
        end_time_stamp = float("inf")
        if start_date is not None:
            start_timestamp = (
                datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        if end_date is not None:
            end_time_stamp = (
                datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        return [
            msg
            for msg in self.messages
            if start_timestamp <= msg.timestamp <= end_time_stamp
        ]


@dataclass
class MessagingApp(App):
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

    name: str | None = None
    conversations: dict[str, Conversation] = field(default_factory=dict)
    # View limit of messages in a conversation
    messages_view_limit: int = 10
    # View limit of conversations when listing conversations
    conversation_view_limit: int = 5

    def __post_init__(self):
        super().__init__(self.name)

    def get_state(self) -> dict[str, Any]:
        return get_state_dict(
            self, ["conversations", "messages_view_limit", "conversation_view_limit"]
        )

    def load_state(self, state_dict: dict[str, Any]):
        self.load_conversations_from_dict(state_dict["conversations"])
        self.messages_view_limit = state_dict["messages_view_limit"]
        self.conversation_view_limit = state_dict["conversation_view_limit"]

    def load_conversations_from_dict(self, conversations_dict):
        for conversation_id in conversations_dict:
            conversation = Conversation(
                conversation_id=conversation_id,
                title=conversations_dict[conversation_id]["title"],
                participants=conversations_dict[conversation_id]["participants"],
            )
            conversation.load_state(conversations_dict[conversation_id])
            self.conversations[conversation_id] = conversation

    def reset(self):
        super().reset()
        self.conversations = {}

    @event_registered(operation_type=OperationType.WRITE)
    def add_conversation(self, conversation: Conversation) -> None:
        """
        Add a conversation to the app.
        :param conversation: The conversation to add.
        """
        assert isinstance(conversation, Conversation), (
            "Conversation must be an instance of Conversation."
        )
        self.conversations[conversation.conversation_id] = conversation

    def add_conversations(self, conversations: list[Conversation]) -> None:
        """
        Add a list of conversations to the app.
        :param conversations: The conversations to add.
        """
        assert all(isinstance(conv, Conversation) for conv in conversations), (
            "All conversations must be an instance of Conversation."
        )
        for conv in conversations:
            self.add_conversation(conv)

    @type_check
    @app_tool()
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def create_conversation(
        self, participants: list[str], title: str | None = None
    ) -> str:
        """
        Create a new conversation with the given participants.
        If title is not provided, it will be set to the participants.
        :param participants: List of participants in the conversation, these are the full names of the contacts. The current user is "Me" and will be added automatically.
        :param title: Optional title for the conversation
        :returns: Id of the created conversation

        :example:
            create_conversation(["John Doe", "Jane Doe", "Bob Roberts"], "My group chat")
        """
        if len(participants) < 1:
            raise Exception("Must have at least one participant")
        participants_set = set(participants)
        participants_set.add("Me")
        conversation = Conversation(
            conversation_id=uuid_hex(self.rng),
            participants=list(participants_set),
            title=title,
        )
        self.conversations[conversation.conversation_id] = conversation
        return conversation.conversation_id

    def apply_conversation_limits(
        self,
        conversations: list[Conversation],
        offset_recent_messages_per_conversation: int,
        limit_recent_messages_per_conversation: int,
    ) -> list[Conversation]:
        if limit_recent_messages_per_conversation > self.messages_view_limit:
            raise ValueError(
                f"Limit must be smaller than the view limit of {self.messages_view_limit} - Please use a smaller limit and use offset to navigate"
            )

        if offset_recent_messages_per_conversation < 0:
            raise ValueError("Offset must be non-negative")

        new_conversations = []
        for conversation in conversations:
            sorted_messages = sorted(
                conversation.messages, key=lambda msg: msg.timestamp, reverse=True
            )
            start_index = offset_recent_messages_per_conversation
            end_index = min(
                len(conversation.messages),
                offset_recent_messages_per_conversation
                + limit_recent_messages_per_conversation,
            )
            new_conversation = Conversation(
                participants=conversation.participants,
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
        limit_recent_messages_per_conversation: int = 5,
    ) -> list[Conversation]:
        """
        List conversations ordered by the most recent modification, considering an offset and view limit.
        e.g. list_recent_conversations(0, 5) will list the 5 most recent conversations.
        :param offset: The starting index from which to list conversations
        :param limit: The number of conversations to list, this number needs to be small otherwise an error will be raised
        :param offset_recent_messages_per_conversation: The starting index from which to list messages in each conversation
        :param limit_recent_messages_per_conversation: The number of messages to list in each conversation, this number needs to
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

        sorted_conversations: list[Conversation] = sorted(
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
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_conversations_by_participant(
        self,
        participant: str,
        offset: int = 0,
        limit: int = 5,
        offset_recent_messages_per_conversation: int = 0,
        limit_recent_messages_per_conversation: int = 5,
    ) -> list[Conversation]:
        """
        List all the conversations with the given participant.
        :param participant: Participant name in the conversation
        :param offset: The starting index from which to list conversations
        :param limit: The number of conversations to list, this number needs to be small otherwise an error will be raised
        :param offset_recent_messages_per_conversation: The starting index from which to list messages in each conversation
        :param limit_recent_messages_per_conversation: The number of messages to list in each conversation, this number needs to be small otherwise an error will be raised
        :returns: List of Conversation details

        :example:
            list_conversations_by_participant("John Doe", 0, 5)
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
            if any(participant in p_fullname for p_fullname in conv.participants)
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
    def send_message(self, conversation_id: str, content: str = "") -> str:
        """
        Send a message to the conversation with the given conversation_id.
        :param conversation_id: Conversation id to send the message to
        :param content: Message content
        :returns: Id of the sent message

        :example:
            send_message("1234567890abcdef", "Hello world!")
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        msg_id = uuid_hex(self.rng)
        timestamp = self.time_manager.time()
        self.conversations[conversation_id].messages.append(  # type: ignore
            Message(
                message_id=msg_id,
                sender="Me",
                timestamp=timestamp,
                content=content,
            )
        )
        self.conversations[conversation_id].update_last_updated(timestamp)
        return msg_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def send_attachment(self, conversation_id: str, filepath: str) -> str:
        """
        Send an attachment to the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param filepath: Path to the attachment to send
        :returns: Message id of the sent attachment

        :example:
            send_attachment("1234567890abcdef", "/path/to/attachment.txt")
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                file_content = base64.b64encode(f.read())
                file_name = os.path.basename(filepath)
                msg_id = uuid_hex(self.rng)
                timestamp = self.time_manager.time()
                self.conversations[conversation_id].messages.append(  # type: ignore
                    FileMessage(
                        message_id=msg_id,
                        sender="Me",
                        timestamp=timestamp,
                        attachment=file_content,
                        attachment_name=file_name,
                    )
                )
                self.conversations[conversation_id].update_last_updated(timestamp)
        else:
            raise Exception(f"File {filepath} does not exist")

        return msg_id

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

        with open(full_path, "wb") as file:
            file.write(file_data)

        return full_path

    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        timestamp: float | None = None,
    ) -> None:
        """
        Send a message to the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param content: Message content
        :returns: None
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if sender not in self.conversations[conversation_id].participants:
            raise Exception(f"Sender {sender} not in conversation")
        timestamp = timestamp if timestamp else self.time_manager.time()
        self.conversations[conversation_id].messages.append(  # type: ignore
            Message(
                message_id=uuid_hex(self.rng),
                sender=sender,
                timestamp=timestamp,
                content=content,
            )
        )
        self.conversations[conversation_id].update_last_updated(timestamp)

    @type_check
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def create_and_add_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
    ) -> str:
        """
        Send a message to the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param sender: Sender of the message. If the sender is the user, it should be "Me"
        :param content: Message content
        :return: conversation id if successful, otherwise raise Exception.
        """
        message_time: str = datetime.fromtimestamp(
            self.time_manager.time(), tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
        time_stamp = (
            datetime.strptime(message_time, "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        self.add_message(conversation_id, sender, content, time_stamp)
        return conversation_id

    @type_check
    @event_registered(operation_type=OperationType.WRITE)
    def add_message_with_time(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        message_time: str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    ) -> str:
        """
        Send a message to the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param sender: Sender of the message
        :param content: Message content
        :param message_time: Time of the message in YYYY-MM-DD HH:MM:SS format
        :return: conversation id if successful, otherwise raise Exception.
        """
        try:
            time_stamp = (
                datetime.strptime(message_time, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        except ValueError:
            raise ValueError(
                "Invalid datetime format for the message time. Please use YYYY-MM-DD HH:MM:SS"
            )
        self.add_message(conversation_id, sender, content, time_stamp)
        return conversation_id

    def delete_future_data(self, timestamp: float) -> None:
        """
        Delete all messages with timestamp greater than the given timestamp.
        :param timestamp: Timestamp to delete messages after
        """
        self.conversations = {
            key: value
            for key, value in self.conversations.items()
            if value.last_updated <= timestamp
        }

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def read_conversation(
        self, conversation_id: str, offset: int = 0, limit: int = 10
    ) -> dict:
        """
        Read the conversation with the given conversation_id.
        Shows the last 'limit' messages after offset. Which means messages between offset and offset + limit will be shown.
        Messages are sorted by timestamp, most recent first.
        :param conversation_id: Conversation id
        :param offset: Offset to shift the view window
        :param limit: Number of messages to show
        :returns: Dict with messages and additional info

        :example:
            read_conversation("1234567890abcdef", 0, 10)
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found")
        if offset < 0:
            raise ValueError("Offset must be positive")
        if offset > len(self.conversations[conversation_id].messages):  # type: ignore
            raise ValueError("Offset is larger than the number of messages")

        conversation = self.conversations[conversation_id]
        # sort messages by timestamp, most recent first
        conversation.messages.sort(key=lambda x: x.timestamp, reverse=True)  # type: ignore

        # compute the indices of the messages to be shown
        start_index = offset
        end_index = min(len(conversation.messages), offset + limit)  # type: ignore
        messages = conversation.messages[start_index:end_index]  # type: ignore
        return {
            "messages": [
                message
                for message in messages
                if isinstance(message, Message)  # TODO: handle attachments
            ],
            "metadata": {
                "message_range": (start_index, end_index),
                "conversation_length": len(conversation.messages),  # type: ignore
                "conversation_id": conversation_id,
                "conversation_title": conversation.title,
            },
        }

    @type_check
    @app_tool()
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_participant_to_conversation(
        self, conversation_id: str, participant: str
    ) -> str:
        """
        Add a participant to the conversation with the given conversation_id.
        :param conversation_id: Conversation id to be updated
        :param participant: Full name of the participant to be added
        :returns: conversation_id of the conversation just updated, if successful, otherwise raise Exception.

        :example:
            add_participant_to_conversation("1234567890abcdef", "John Doe")
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if participant in self.conversations[conversation_id].participants:
            raise Exception(f"Participant {participant} already in conversation")
        self.conversations[conversation_id].participants.append(participant)
        return conversation_id

    @type_check
    @app_tool()
    @data_tool()
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def remove_participant_from_conversation(
        self, conversation_id: str, participant: str
    ) -> str:
        """
        Remove a participant from the conversation with the given conversation_id.
        :param conversation_id: Conversation id
        :param participant: Full name of the participant to be removed
        :returns: conversation_id of the conversation just updated, if successful, otherwise raise Exception.

        :example:
            remove_participant_from_conversation("1234567890abcdef", "John Doe")
        """
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation with id {conversation_id} not found")
        if participant not in self.conversations[conversation_id].participants:
            raise Exception(f"Participant {participant} not in conversation")
        self.conversations[conversation_id].participants.remove(participant)
        return conversation_id

    def get_all_conversations(self) -> list[Conversation]:
        """
        Get all conversations.
        :returns: List of Conversation objects
        """
        sorted_conversations = sorted(self.conversations.items())
        return [conv for _, conv in sorted_conversations]

    @type_check
    @app_tool()
    @data_tool()
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
                results.append(conversation)

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
        conversation: Conversation,
        query: str,
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> bool:
        """
        Helper method to check if a conversation matches the query.
        """
        # Search in participants
        if any(
            query in participant.lower() for participant in conversation.participants
        ):
            return True

        # Search in title
        if conversation.title and query in conversation.title.lower():
            return True

        # Search in messages
        return any(
            isinstance(message, Message) and query in message.content.lower()
            for message in conversation.get_messages_in_date_range(min_date, max_date)
        )

    def _regex_conversation_matches(
        self,
        conversation: Conversation,
        get_match: Callable[[str], re.Match | None],
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> bool:
        """
        Helper method to check if a conversation matches the query using regex.
        """
        if any(
            get_match(participant.lower()) for participant in conversation.participants
        ):
            return True

        # Search in title
        if conversation.title is not None and get_match(conversation.title.lower()):
            return True

            # Search in messages
        if any(
            isinstance(message, Message) and get_match(message.content)
            for message in conversation.get_messages_in_date_range(min_date, max_date)
        ):
            return True
        return False
