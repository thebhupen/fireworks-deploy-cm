# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from enum import Enum

from are.simulation.validation.prompts import PER_TOOL_EVALUATION_CRITERIA


class ToolRegistry(dict):
    """
    A registry for tool argument checker types.
    """

    def __init__(
        self,
        initial_registry=None,
        app_alias: dict[str, list[str]] | None = None,
        tool_alias: dict[str, list[str]] | None = None,
    ):
        """
        Initialize the registry.
        Args:
            initial_registry (dict): The initial registry. Defaults to None.
            app_alias (dict): The app alias dictionary.
            tool_alias (dict): The tool alias dictionary.
        """
        super().__init__(initial_registry or {})
        self.add_aliases(
            app_alias=app_alias,
            tool_alias=tool_alias,
        )

    def add_tool_alias(self, original_function: str, alias_function: str):
        """
        Add an alias to the registry.
        Args:
            original_function (str): The original function name.
            alias (str): The alias name.
        """
        if original_function in self:
            self[alias_function] = self[original_function]
        else:
            raise ValueError(
                f"Original function '{original_function}' not found in registry"
            )

    def add_app_alias(self, original_app: str, alias_app: str):
        """
        Add an alias app to the registry.
        Args:
            original_app (str): The original app name.
            alias_app (str): The alias name.
        """
        for function_name, data in self.copy().items():
            if original_app == function_name.split("__")[0]:
                self[f"{alias_app}__{function_name.split('__')[1]}"] = data

    def add_aliases(
        self,
        tool_alias: dict[str, list[str]] | None = None,
        app_alias: dict[str, list[str]] | None = None,
    ):
        """
        Add aliases to the registry.
        Becarefull, app alias are added after the tool alias.
        Args:
            app_alias (dict): The app alias dictionary.
            tool_alias (dict): The tool alias dictionary.
        """
        if app_alias is None:
            app_alias = {}
        if tool_alias is None:
            tool_alias = {}
        # Add tool aliases
        for original_tool, alias_tool in tool_alias.items():
            if not isinstance(alias_tool, list):
                alias_tool = [alias_tool]
            for alias in alias_tool:
                self.add_tool_alias(
                    original_function=original_tool,
                    alias_function=alias,
                )
        # Add app aliases
        for original_app, alias_app in app_alias.items():
            if not isinstance(alias_app, list):
                alias_app = [alias_app]
            for alias in alias_app:
                self.add_app_alias(
                    original_app=original_app,
                    alias_app=alias,
                )


# Tool checker
class CheckerType(str, Enum):
    eq_checker = "eq_checker"
    unordered_list_checker = "unordered_list_checker"
    list_attendees_checker = "list_attendees_checker"
    datetime_checker = "datetime_checker"
    phone_number_checker = "phone_number_checker"
    eq_str_strip_checker = "eq_str_strip_checker"
    llm_checker = "llm_checker"
    path_checker = "path_checker"
    unordered_path_list_checker = "unordered_path_list_checker"
    hard_checkers = [
        eq_checker,
        unordered_list_checker,
        datetime_checker,
        list_attendees_checker,
        phone_number_checker,
        eq_str_strip_checker,
        path_checker,
        unordered_path_list_checker,
    ]
    contain_any_checker = "contain_any_checker"
    contain_all_checker = "contain_all_checker"
    scripted_checkers = [contain_any_checker, contain_all_checker]

    def is_hard(self):
        return self in self.hard_checkers

    def is_scripted(self):
        return self.value in self.scripted_checkers.value


class ToolArgCheckerTypeRegistry(ToolRegistry):
    """
    A registry for checker types.
    """


# Default tool checker type registry
PER_TOOL_ARG_TO_CHERCKER_TYPE = {
    "ApartmentListingApp__save_apartment": {
        "apartment_id": CheckerType.eq_checker,
    },
    "ApartmentListingApp__remove_saved_apartment": {
        "apartment_id": CheckerType.eq_checker,
    },
    "CalendarApp__add_calendar_event": {
        "attendees": CheckerType.list_attendees_checker,
        "end_datetime": CheckerType.datetime_checker,
        "start_datetime": CheckerType.datetime_checker,
        "title": CheckerType.llm_checker,
        "description": CheckerType.llm_checker,
        "location": CheckerType.llm_checker,
    },
    "CalendarApp__delete_calendar_event": {
        "event_id": CheckerType.eq_checker,
    },
    "ShoppingApp__checkout": {
        "discount_code": CheckerType.eq_str_strip_checker,
    },
    "ShoppingApp__add_to_cart": {
        "item_id": CheckerType.eq_checker,
        "quantity": CheckerType.eq_checker,
    },
    "ShoppingApp__remove_from_cart": {
        "item_id": CheckerType.eq_checker,
        "quantity": CheckerType.eq_checker,
    },
    "ShoppingApp__cancel_order": {
        "order_id": CheckerType.eq_checker,
    },
    "ContactsApp__delete_contact": {
        "contact_id": CheckerType.eq_checker,
    },
    "ContactsApp__add_new_contact": {
        "first_name": CheckerType.eq_str_strip_checker,
        "last_name": CheckerType.eq_str_strip_checker,
        "email": CheckerType.eq_str_strip_checker,
        "phone": CheckerType.phone_number_checker,
    },
    "ContactsApp__edit_contact": {
        "contact_id": CheckerType.eq_checker,
        "updates": CheckerType.llm_checker,
    },
    "EmailClientApp__reply_to_email": {
        "email_id": CheckerType.eq_checker,
        "content": CheckerType.llm_checker,
        "attachment_paths": CheckerType.unordered_path_list_checker,
    },
    "EmailClientApp__delete_email": {
        "email_id": CheckerType.eq_checker,
    },
    "EmailClientApp__send_email": {
        "recipients": CheckerType.unordered_list_checker,
        "cc": CheckerType.unordered_list_checker,
        "attachment_paths": CheckerType.unordered_path_list_checker,
        "subject": CheckerType.llm_checker,
        "content": CheckerType.llm_checker,
    },
    "EmailClientApp__move_email": {
        "email_id": CheckerType.eq_checker,
        "source_folder_name": CheckerType.path_checker,
        "dest_folder_name": CheckerType.path_checker,
    },
    "EmailClientApp__forward_email": {
        "email_id": CheckerType.eq_checker,
        "recipients": CheckerType.unordered_list_checker,
        "folder_name": CheckerType.eq_checker,
    },
    "EmailClientApp__download_attachments": {
        "email_id": CheckerType.eq_checker,
        "folder_name": CheckerType.eq_checker,
        "path_to_save": CheckerType.path_checker,
    },
    "CabApp__order_ride": {
        "start_location": CheckerType.llm_checker,
        "end_location": CheckerType.llm_checker,
        "service_type": CheckerType.eq_checker,
        "ride_time": CheckerType.datetime_checker,
    },
    "CabApp__user_cancel_ride": {},
    "MessagingApp__create_conversation": {
        "participants": CheckerType.unordered_list_checker,
    },
    "MessagingApp__add_participant_to_conversation": {
        "conversation_id": CheckerType.eq_checker,
        "participant": CheckerType.eq_checker,
    },
    "MessagingApp__remove_participant_from_conversation": {
        "conversation_id": CheckerType.eq_checker,
        "participant": CheckerType.eq_checker,
    },
    "MessagingApp__send_message": {
        "conversation_id": CheckerType.eq_checker,
        "content": CheckerType.llm_checker,
    },
    "MessagingAppV2__send_message": {
        "user_id": CheckerType.eq_checker,
        "content": CheckerType.llm_checker,
        "attachment_path": CheckerType.path_checker,
    },
    "MessagingAppV2__send_message_to_group_conversation": {
        "conversation_id": CheckerType.eq_checker,
        "content": CheckerType.llm_checker,
        "attachment_path": CheckerType.path_checker,
    },
    "MessagingAppV2__create_group_conversation": {
        "user_ids": CheckerType.unordered_list_checker,
        "title": CheckerType.llm_checker,
    },
    "MessagingAppV2__add_participant_to_conversation": {
        "conversation_id": CheckerType.eq_checker,
        "user_id": CheckerType.eq_checker,
    },
    "MessagingAppV2__remove_participant_from_conversation": {
        "conversation_id": CheckerType.eq_checker,
        "user_id": CheckerType.eq_checker,
    },
    "MessagingAppV2__change_conversation_title": {
        "conversation_id": CheckerType.eq_checker,
        "title": CheckerType.llm_checker,
    },
    "SandboxLocalFileSystem__mv": {
        "path1": CheckerType.path_checker,
        "path2": CheckerType.path_checker,
    },
    "SandboxLocalFileSystem__open": {
        "path": CheckerType.path_checker,
        "mode": CheckerType.eq_checker,
    },
    "SandboxLocalFileSystem__mkdir": {
        "path": CheckerType.path_checker,
    },
    "SandboxLocalFileSystem__rm": {
        "path": CheckerType.path_checker,
        "recursive": CheckerType.eq_checker,
    },
    "SandboxLocalFileSystem__rmdir": {
        "path": CheckerType.path_checker,
    },
    "AgentUserInterface__send_message_to_user": {
        "content": CheckerType.llm_checker,
    },
    "VirtualFileSystem__open": {
        "path": CheckerType.path_checker,
        "mode": CheckerType.eq_checker,
    },
    "VirtualFileSystem__mkdir": {
        "path": CheckerType.path_checker,
        "create_recursive": CheckerType.eq_checker,
    },
    "VirtualFileSystem__mv": {
        "path1": CheckerType.path_checker,
        "path2": CheckerType.path_checker,
    },
    "VirtualFileSystem__rm": {
        "path": CheckerType.path_checker,
        "recursive": CheckerType.eq_checker,
    },
    "VirtualFileSystem__rmdir": {
        "path": CheckerType.path_checker,
    },
}

APP_ALIAS = {
    "EmailClientApp": ["EmailClientV2", "Mail", "Emails"],
    "ApartmentListingApp": ["RentAFlat"],
    "ContactsApp": ["Contacts"],
    "MessagingApp": [],
    "MessagingAppV2": ["Messages", "Chats"],
    "CalendarApp": ["Calendar"],
    "ShoppingApp": ["Shopping"],
    "CabApp": ["Cabs"],
    "SandboxLocalFileSystem": ["Files"],
}


# Default tool checker type registry
TOOL_ARG_CHECKER_TYPE_REGISTRY = ToolArgCheckerTypeRegistry(
    initial_registry=PER_TOOL_ARG_TO_CHERCKER_TYPE,
    app_alias=APP_ALIAS,
    tool_alias={"SandboxLocalFileSystem__mkdir": ["SandBoxLocalFileSystem__makedirs"]},
)


# Tool criteria
class ToolCriteriaRegistry(ToolArgCheckerTypeRegistry):
    """
    A registry for tool criteria.
    """


TOOL_ALIAS = {
    "MessagingApp__send_message": [
        "MessagingAppV2__send_message",
        "MessagingAppV2__send_message_to_group_conversation",
    ],
    "MessagingApp__create_conversation": [
        "MessagingAppV2__create_group_conversation",
        "MessagingAppV2__change_conversation_title",
    ],
}

# Default tool criteria registry
TOOL_EVALUATION_CRITERIA_REGISTRY = ToolCriteriaRegistry(
    initial_registry=PER_TOOL_EVALUATION_CRITERIA,
    app_alias=APP_ALIAS,
    tool_alias=TOOL_ALIAS,  # type: ignore
)


# Soft checkers
class SoftCheckerType(str, Enum):
    content_checker = "content_checker"
    sanity_checker = "sanity_checker"
    signature_checker = "signature_checker"
    placeholder_checker = "placeholder_checker"
    cab_checker = "cab_checker"
    event_checker = "event_checker"
    message_checker = "message_checker"
    email_checker = "email_checker"
    user_message_checker = "user_message_checker"
    tone_checker = "tone_checker"

    @property
    def need_subtask(self) -> bool:
        return self in {
            self.content_checker,
            self.user_message_checker,
            self.event_checker,
            self.sanity_checker,
        }


PER_TOOL_TO_SOFT_CHECKER_TYPES = {
    "CalendarApp__add_calendar_event": [SoftCheckerType.event_checker],
    "EmailClientApp__send_email": [
        SoftCheckerType.placeholder_checker,
        SoftCheckerType.signature_checker,
        SoftCheckerType.tone_checker,
        SoftCheckerType.email_checker,
    ],
    "EmailClientApp__reply_to_email": [
        SoftCheckerType.placeholder_checker,
        SoftCheckerType.signature_checker,
        SoftCheckerType.tone_checker,
        SoftCheckerType.email_checker,
    ],
    "MessagingApp__send_message": [
        SoftCheckerType.placeholder_checker,
        SoftCheckerType.tone_checker,
        SoftCheckerType.message_checker,
    ],
    "CabApp__order_ride": [SoftCheckerType.cab_checker],
    "AgentUserInterface__send_message_to_user": [
        SoftCheckerType.sanity_checker,
        SoftCheckerType.user_message_checker,
    ],
    "MessagingApp__create_conversation": [
        SoftCheckerType.content_checker,
    ],
}


class ToolSoftCheckerTypeRegistry(ToolArgCheckerTypeRegistry):
    """
    A registry for soft checkers.
    """


TOOL_SOFT_CHECKER_TYPE_REGISTRY = ToolSoftCheckerTypeRegistry(
    initial_registry=PER_TOOL_TO_SOFT_CHECKER_TYPES,
    tool_alias=TOOL_ALIAS,  # type: ignore
    app_alias=APP_ALIAS,  # type: ignore
)
