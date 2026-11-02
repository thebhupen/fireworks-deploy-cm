# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import random
from dataclasses import dataclass, field
from typing import cast

import numpy as np

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.apartment_listing import ApartmentListingApp
from are.simulation.apps.email_client import EmailClientApp
from are.simulation.apps.messaging import MessagingApp
from are.simulation.apps.messaging_v2 import MessagingAppV2
from are.simulation.apps.shopping import ShoppingApp
from are.simulation.types import (
    AbstractEnvironment,
    ConditionCheckEvent,
    EventRegisterer,
    EventType,
)

logger = logging.getLogger(__name__)

ENV_EVENT_EXPANSION_TAG = "env_expansion"
# ENV events are scheduled using a Poisson process with finite horizon
ENV_EVENT_DEFAULT_HORIZON = 360


def start_simulation_condition(env: AbstractEnvironment) -> bool:
    # check that the user sent a message to the agent
    return any(
        event.app_class_name() == AgentUserInterface.__name__
        and event.function_name() == "send_message_to_agent"
        for event in env.event_log.list_view()
        if event.event_type == EventType.USER
    )


def default_weight_per_app_class() -> dict[str, float]:
    return {
        "EmailClientApp": 1.0,
        "ApartmentListingApp": 1.0,
        "MessagingApp": 1.0,
        "MessagingAppV2": 1.0,
        "ShoppingApp": 1.0,
    }


@dataclass
class EnvEventsConfig:
    """
    Configuration class for controlling environmental event generation and scheduling in simulations.

    This class defines parameters that control how background events (messages, emails, shopping updates,
    apartment listings) are automatically generated and scheduled during scenario execution. Events are
    scheduled using a Poisson process to simulate realistic timing patterns.

    These environmental events add noise to scenarios by generating synthetic background activity that is
    unrelated to the main scenario task. This simulates a more realistic environment where agents receive
    distracting notifications and updates while trying to complete their primary objective.

    Attributes:
        num_env_events_per_minute: Rate of environmental events to generate per minute of simulation time.
            Higher values create more noise and distractions, making the scenario more challenging by
            increasing the volume of irrelevant background activity.
        env_events_seed: Random seed for reproducible event sampling and Poisson scheduling. Different
            seeds will generate different patterns of noise events while maintaining the same overall
            distribution and timing characteristics.
        n_message_events_per_conversation: Maximum number of message events to generate per conversation.
            Higher values create longer conversation threads in messaging apps, adding more textual noise
            that the agent must filter through when looking for relevant information.
        n_item_events_per_product: Maximum number of item events to generate per shopping product.
            Higher values create more product variants and options in shopping apps, increasing the
            complexity of product catalogs and making it harder to find specific items.
        weight_per_app_class: Relative weights for distributing events across different app types.
            Adjusting these weights changes which types of noise dominate - higher email weights create
            more inbox clutter, higher messaging weights create more chat notifications, etc.
    """

    num_env_events_per_minute: int = 10
    # random seed for sampling ENV events from the scenario universe data and Poisson scheduling
    env_events_seed: int = 0

    # scheduling parameters
    n_message_events_per_conversation: int = 4
    n_item_events_per_product: int = 2
    weight_per_app_class: dict[str, float] = field(
        default_factory=default_weight_per_app_class
    )


class EnvEventsExpander:
    def __init__(
        self,
        env_events_config: EnvEventsConfig,
    ) -> None:
        self.config = env_events_config

    def get_num_env_events_per_app(
        self, num_env_events: int, app_names: list[str]
    ) -> dict[str, int]:
        # Resolve app names to their canonical form
        self.resolved_app_names = self._resolve_app_names(app_names)

        # Calculate the number of events per app
        num_env_events_per_app = {}
        total_weight = sum(
            self.config.weight_per_app_class.get(self.resolved_app_names[app], 0)
            for app in app_names
        )

        for app in app_names:
            weight = self.config.weight_per_app_class.get(
                self.resolved_app_names[app], 0
            )
            num_env_events_per_app[app] = int((weight / total_weight) * num_env_events)
        return num_env_events_per_app

    def _resolve_app_names(self, app_names: list[str]) -> dict[str, str]:
        # Import here to avoid circular import
        from are.simulation.validation.constants import APP_ALIAS

        resolved_names = {}
        for app in app_names:
            for canonical_name, aliases in APP_ALIAS.items():
                if app == canonical_name or app in (
                    aliases if isinstance(aliases, list) else [aliases]
                ):
                    resolved_names[app] = canonical_name
                    break
        return resolved_names

    def add_env_events_to_scenario(self, scenario) -> None:  # type: ignore
        """
        Expands the scenario in-place with ENV events.
        :param scenario: scenario to expand
        """
        augmentation_data = scenario.augmentation_data or {}
        apps_augmentation_data = (
            augmentation_data["apps"] if "apps" in augmentation_data else []
        )

        logger.warning(
            f"Adding {self.config.num_env_events_per_minute} env events per minute, total duration: {scenario.duration} seconds"
        )

        d_events = dict()
        add_start_event_flag = False
        if scenario.events:
            # first processed event without parent
            d_events["start_event"] = scenario.events[0]
        else:
            # otherwise, wait for first message from the user
            d_events["start_event"] = ConditionCheckEvent.from_condition(
                start_simulation_condition, every_tick=3
            )
            add_start_event_flag = True
        assert d_events["start_event"].dependencies == [], (
            "start event should have no dependencies"
        )

        duration = scenario.duration if scenario.duration else ENV_EVENT_DEFAULT_HORIZON

        # scheduling ENV events using an exponential distribution
        np_rng = np.random.default_rng(self.config.env_events_seed)
        rng = random.Random(self.config.env_events_seed)

        app_names = [d["name"] for d in apps_augmentation_data]
        num_env_events = int(self.config.num_env_events_per_minute * duration / 60)
        num_env_events_per_app = self.get_num_env_events_per_app(
            num_env_events, app_names
        )

        messaging_apps = ["MessagingAppV2", "Chats", "Messages"]
        email_apps = ["EmailClientV2", "EmailClientApp", "Mail"]
        shopping_apps = ["Shopping", "ShoppingApp"]
        apartment_apps = ["RentAFlat", "ApartmentListingApp"]

        with EventRegisterer.capture_mode():
            for d in apps_augmentation_data:
                # schedule messaging events
                app_name = self.resolved_app_names.get(d["name"], d["name"])
                if d["name"] in messaging_apps:
                    app = (
                        cast(MessagingApp, scenario.get_app(d["name"]))
                        if "V2" not in app_name  # type: ignore
                        else cast(MessagingAppV2, scenario.get_app(d["name"]))
                    )
                    conversations = list(d["app_state"]["conversations"].values())
                    # number of conversations to update
                    n_conversation_events = max(
                        num_env_events_per_app[d["name"]]
                        // self.config.n_message_events_per_conversation,
                        len(conversations),
                    )
                    n_conversation_events = min(
                        n_conversation_events,
                        len(conversations),
                    )
                    conversations = rng.sample(
                        conversations,
                        k=n_conversation_events,
                    )
                    average_rate = n_conversation_events / duration
                    inter_arrival_times = np_rng.exponential(
                        scale=1 / average_rate, size=n_conversation_events
                    )
                    ticks = np.cumsum(inter_arrival_times)
                    for i, (tick, conversation) in enumerate(zip(ticks, conversations)):
                        if tick > duration:
                            break
                        n_messages = len(conversation["messages"])
                        if n_messages == 0:
                            continue
                        n_message_events = min(
                            n_messages,
                            self.config.n_message_events_per_conversation,
                        )
                        message_average_rate = n_message_events / (duration - tick)
                        message_inter_arrival_times = np_rng.exponential(
                            scale=1 / message_average_rate, size=n_message_events
                        )
                        for i, message in enumerate(conversation["messages"]):
                            if i >= n_message_events:
                                break
                            if "V2" not in app_name:  # type: ignore
                                d_events[
                                    f"{d['name']}_{conversation['conversation_id']}_{i}"
                                ] = app.create_and_add_message(
                                    conversation_id=conversation["conversation_id"],
                                    sender=message["sender"],
                                    content=message["content"],
                                )
                            else:
                                d_events[
                                    f"{d['name']}_{conversation['conversation_id']}_{i}"
                                ] = app.create_and_add_message(
                                    conversation_id=conversation["conversation_id"],
                                    sender_id=message["sender_id"],
                                    content=message["content"],
                                )
                            if i == 0:
                                d_events[
                                    f"{d['name']}_{conversation['conversation_id']}_{i}"
                                ].depends_on(
                                    d_events["start_event"],
                                    delay_seconds=tick,
                                )
                            else:
                                d_events[
                                    f"{d['name']}_{conversation['conversation_id']}_{i}"
                                ].depends_on(
                                    d_events[
                                        f"{d['name']}_{conversation['conversation_id']}_{i - 1}"
                                    ],
                                    delay_seconds=message_inter_arrival_times[i - 1],
                                )
                # schedule email events
                if d["name"] in email_apps:
                    email_client = cast(EmailClientApp, scenario.get_app(d["name"]))
                    emails = d["app_state"]["folders"]["INBOX"]["emails"]
                    rng.shuffle(emails)
                    n_emails = len(emails)
                    if n_emails == 0:
                        continue

                    n_events = min(n_emails, num_env_events_per_app[d["name"]])
                    average_rate = n_events / duration
                    inter_arrival_times = np_rng.exponential(
                        scale=1 / average_rate, size=n_events
                    )
                    ticks = np.cumsum(inter_arrival_times)
                    for i, (tick, email) in enumerate(zip(ticks, emails)):
                        d_events[f"email_{email['email_id']}"] = (
                            email_client.create_and_add_email(
                                sender=email["sender"],
                                recipients=email["recipients"],
                                subject=email["subject"],
                                content=email["content"],
                                folder_name="INBOX",
                            ).depends_on(d_events["start_event"], delay_seconds=tick)
                        )

                # schedule shopping events
                if d["name"] in shopping_apps:
                    shopping = cast(ShoppingApp, scenario.get_app(d["name"]))
                    n_products = len(d["app_state"]["products"])
                    product_list = list(d["app_state"]["products"].values())
                    rng.shuffle(product_list)
                    if n_products == 0:
                        continue

                    n_events = min(
                        n_products,
                        num_env_events_per_app[d["name"]]
                        // self.config.n_item_events_per_product,
                    )
                    average_rate = n_events / duration
                    inter_arrival_times = np_rng.exponential(
                        scale=1 / average_rate, size=n_events
                    )
                    ticks = np.cumsum(inter_arrival_times)
                    for i, (tick, product) in enumerate(zip(ticks, product_list)):
                        if tick > duration:
                            continue
                        d_events[f"shopping_product_{product['product_id']}"] = (
                            shopping.add_product(
                                name=product["name"],
                            )
                        ).depends_on(d_events["start_event"], delay_seconds=tick)

                        n_items = len(product["variants"])
                        if n_items == 0:
                            continue
                        n_item_events = min(
                            n_items, self.config.n_item_events_per_product
                        )
                        item_average_rate = n_item_events / (duration - tick)
                        item_inter_arrival_times = np_rng.exponential(
                            scale=1 / item_average_rate, size=n_item_events
                        )
                        item_ticks = np.cumsum(item_inter_arrival_times)
                        for j, (item_tick, item) in enumerate(
                            zip(item_ticks, product["variants"].values())
                        ):
                            d_events[f"shopping_item_{item['item_id']}"] = (
                                shopping.add_item_to_product(
                                    product_id="{{"
                                    + f"{ENV_EVENT_EXPANSION_TAG}_shopping_product_{product['product_id']}"
                                    + "}}",
                                    price=item["price"],
                                    available=item["available"],
                                    options=item["options"],
                                ).depends_on(
                                    d_events[
                                        f"shopping_product_{product['product_id']}"
                                    ],
                                    delay_seconds=item_tick,
                                )
                            )

                    for i, (item_id, discount_codes) in enumerate(
                        d["app_state"]["discount_codes"].items()
                    ):
                        discount_codes = cast(dict[str, float], discount_codes)
                        discount_codes: dict[str, float] = {
                            str(k): float(v) for k, v in discount_codes.items()
                        }
                        delay_tick = np_rng.exponential(scale=duration // 2, size=1)[0]
                        if f"shopping_item_{item_id}" in d_events:
                            for code, value in discount_codes.items():
                                discount_code = {code: value}
                                d_events[f"shopping_discount_code_{item_id}_{code}"] = (
                                    shopping.add_discount_code(
                                        item_id="{{"
                                        + f"{ENV_EVENT_EXPANSION_TAG}_shopping_item_{item_id}"
                                        + "}}",
                                        discount_code=discount_code,
                                    )
                                ).depends_on(
                                    d_events[f"shopping_item_{item_id}"],
                                    delay_seconds=delay_tick,
                                )

                # schedule apartment events
                if d["name"] in apartment_apps:
                    rent_a_flat = cast(ApartmentListingApp, scenario.get_app(d["name"]))
                    apartment_list = list(d["app_state"]["apartments"].values())
                    rng.shuffle(apartment_list)
                    n_apartments = len(apartment_list)
                    if n_apartments == 0:
                        continue
                    n_events = min(n_apartments, num_env_events_per_app[d["name"]])
                    average_rate = n_events / duration
                    inter_arrival_times = np_rng.exponential(
                        scale=1 / average_rate, size=n_events
                    )
                    ticks = np.cumsum(inter_arrival_times)
                    for i, (tick, apartment) in enumerate(zip(ticks, apartment_list)):
                        apartment["number_of_bedrooms"] = apartment["bedrooms"]
                        apartment["number_of_bathrooms"] = apartment["bathrooms"]
                        del apartment["bedrooms"]
                        del apartment["bathrooms"]
                        if "apartment_id" in apartment:
                            del apartment["apartment_id"]
                        apartment["price"] = float(apartment["price"])
                        d_events[f"apartment_{i}"] = (
                            rent_a_flat.add_new_apartment(**apartment)
                        ).depends_on(d_events["start_event"], delay_seconds=tick)

            if not add_start_event_flag:
                del d_events["start_event"]  # already added to scenario.events

            scenario.events += [
                e.with_id(f"{ENV_EVENT_EXPANSION_TAG}_{key}")
                for key, e in d_events.items()
            ]

            logger.warning(
                f"Added {len(d_events)} env events to the scenario, total {len(scenario.events)} events"
            )
