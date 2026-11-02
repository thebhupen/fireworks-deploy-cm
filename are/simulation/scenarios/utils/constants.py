# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging

from are.simulation.scenarios.utils.registry import registry

logger = logging.getLogger(__name__)

ALL_SCENARIOS = registry.get_all_scenarios()

MESSAGE_VERSION_TO_SCENARIO = {
    "v1": [
        "scenario_ask_day_messaging",
        "scenario_book_cab_service",
        "scenario_book_cab_location_ambig",
        "scenario_calendar_contact_ambig",
        "scenario_calendar_email_contact",
        "scenario_delete_calendar_event",
        "scenario_delete_email",
        "scenario_email_month",
        "scenario_find_availability",
        "scenario_keyword_count",
        "scenario_message_find_availability",
        "scenario_restaurant_message",
        "scenario_send_conv_message",
        "scenario_send_email_contact",
        "scenario_send_message_first_name",
        "scenario_spotify_calendar",
        "scenario_spotify_message",
        "scenario_topk_shopping",
        "scenario_web_search_message",
        "scenario_web_search_spotify",
        "scenario_contextual_bench",
        "scenario_search_messages_1",
        "scenario_search_messages_2",
        "scenario_time_based_single_task",
        "scenario_time_based_multi_timescale",
        "scenario_time_based_same_timescale",
        "scenario_time_based_and_easy_task_seq",
        "scenario_time_based_and_easy_task_async",
        "scenario_time_based_retro",
        "scenario_time_based_one_time_single_task",
        "scenario_time_based_one_time_and_easy_task_seq",
        "scenario_event_based_single_task",
        "scenario_event_based_and_easy_task_seq",
        "scenario_event_based_and_easy_task_async",
        "scenario_event_based_and_retro",
        "scenario_every_datetime_single_task",
        "scenario_every_datetime_and_easy_task_seq",
        "scenario_time_based_single_task_long",
        "scenario_add_participant_nationality",
        "scenario_apartment_viewing_planner",
        "scenario_book_cab_between_events",
        "scenario_find_apartment_for_events",
        "scenario_migrate_inactive_conversations",
        "scenario_product_restock",
        "scenario_product_sales_event",
        "scenario_schedule_reverse_rides",
        "scenario_contacts_purchase",
    ],
    "v2": [
        "scenario_search_messages_hideseek_code",
        "scenario_search_messages_hideseek",
        "scenario_apartment_alert_message_2",
        "scenario_apartment_alert_message_and_shopping_message_2",
        "scenario_recurrent_cab",
        "scenario_count_new_apartments_retro",
        "scenario_recurrent_cab_and_shopping_message",
        "scenario_email_filtering_automation",
        "scenario_email_filtering_automation_and_shopping_message",
        "scenario_concert_ticket_shotgun",
        "scenario_followup_message",
        "scenario_followup_message_and_shopping_message",
        "scenario_time_based_single_task_v2",
        "scenario_every_datetime_single_task_v2",
        "scenario_every_datetime_summary_v2",
    ],
}

SCENARIO_TO_MESSAGE_VERSION = {
    scenario: version
    for version, scenarios in MESSAGE_VERSION_TO_SCENARIO.items()
    for scenario in scenarios
}

UNIVERSE_VERSION_TO_IDS = {
    "train_v1": [f"universe_{i}" for i in range(0, 20)],
    "demo_v1": ["personal_assistant", "universe_demo", "universe_yann"],
    "benchmark_v2": [f"universe_{i}" for i in range(21, 31)],
    "train_v2": ["universe_20"] + [f"universe_{i}" for i in range(31, 41)],
}

UNIVERSE_ID_TO_VERSION = {
    universe_id: version
    for version, universe_ids in UNIVERSE_VERSION_TO_IDS.items()
    for universe_id in universe_ids
}
