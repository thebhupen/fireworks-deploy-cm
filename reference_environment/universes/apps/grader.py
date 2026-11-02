"""Verifier settings for every write tool of the Bharat apps (app_schemas.md x.5).

ARE's judge looks a tool up as ``<AppClassName>__<function>`` and refuses
oracle actions it has no settings for, so every write tool must appear here.
Arguments checked with ``llm_checker`` are only judged when the tool also has
a soft checker; ``content_checker`` judges free text against the task.
"""

from __future__ import annotations

from are.simulation.validation.constants import (
    TOOL_ARG_CHECKER_TYPE_REGISTRY,
    TOOL_SOFT_CHECKER_TYPE_REGISTRY,
    CheckerType,
    SoftCheckerType,
)
from are.simulation.validation.utils.llm_utils import LLMChecker

EQ = CheckerType.eq_checker
STRIP = CheckerType.eq_str_strip_checker
LIST = CheckerType.unordered_list_checker
WHEN = CheckerType.datetime_checker
PHONE = CheckerType.phone_number_checker
LLM = CheckerType.llm_checker

SHOPPING_WRITES = {
    "add_to_cart": {"item_id": EQ, "quantity": EQ},
    "remove_from_cart": {"item_id": EQ, "quantity": EQ},
    "checkout": {"address_id": EQ, "payment": EQ, "discount_code": STRIP},
    "cancel_order": {"order_id": EQ},
    "request_return": {"order_id": EQ, "item_id": EQ, "reason": LLM},
    "add_to_wishlist": {"item_id": EQ},
    "remove_from_wishlist": {"item_id": EQ},
    "add_address": {"label": EQ, "line1": LLM, "area": LLM, "city": LLM, "pincode": EQ, "phone": PHONE},
}

WRITE_TOOL_CHECKERS: dict[str, dict[str, dict[str, CheckerType]]] = {
    "PaySetuApp": {
        "send_money": {"upi_id": EQ, "amount": EQ, "payment": EQ, "note": LLM},
        "request_money": {"upi_id": EQ, "amount": EQ, "note": LLM},
        "pay_request": {"request_id": EQ, "payment": EQ},
        "decline_request": {"request_id": EQ},
        "add_payee": {"name": LLM, "upi_id": EQ, "phone": PHONE},
    },
    "RailMitraApp": {
        "book_ticket": {
            "train_number": EQ,
            "journey_date": EQ,
            "from_station": EQ,
            "to_station": EQ,
            "travel_class": EQ,
            "passenger_ids": LIST,
            "payment": EQ,
            "quota": EQ,
        },
        "cancel_ticket": {"pnr": EQ, "passenger_ids": LIST},
        "add_saved_passenger": {"name": LLM, "age": EQ, "gender": EQ, "berth_preference": EQ},
    },
    "SafarHubApp": {
        "book_flight": {"flight_id": EQ, "date": EQ, "fare_family": EQ, "traveller_ids": LIST, "payment": EQ},
        "book_hotel": {
            "hotel_id": EQ,
            "room_type": EQ,
            "check_in": EQ,
            "check_out": EQ,
            "rooms": EQ,
            "adults": EQ,
            "children": EQ,
            "payment": EQ,
        },
        "book_package": {"package_id": EQ, "start_date": EQ, "traveller_ids": LIST, "payment": EQ},
        "cancel_booking": {"booking_id": EQ},
        "add_saved_traveller": {"name": LLM, "date_of_birth": EQ, "gender": EQ, "type": EQ},
    },
    "KartBazaarApp": SHOPPING_WRITES,
    "StyleGaliApp": SHOPPING_WRITES,
    "ThaliDashApp": {
        "add_to_cart": {"item_id": EQ, "quantity": EQ},
        "remove_from_cart": {"item_id": EQ, "quantity": EQ},
        "clear_cart": {},
        "place_order": {"address_id": EQ, "payment": EQ, "coupon_code": STRIP, "delivery_instructions": LLM},
        "cancel_order": {"order_id": EQ},
        "rate_order": {"order_id": EQ, "rating": EQ},
        "book_table": {"restaurant_id": EQ, "datetime": WHEN, "guests": EQ, "special_request": LLM},
        "cancel_reservation": {"reservation_id": EQ},
    },
    "SehatCareApp": {
        "book_consultation": {"doctor_id": EQ, "slot_id": EQ, "patient_id": EQ, "payment": EQ},
        "book_lab_test": {"test_ids": LIST, "slot_id": EQ, "patient_id": EQ, "payment": EQ, "address_id": EQ},
        "reschedule_appointment": {"appointment_id": EQ, "new_slot_id": EQ},
        "cancel_appointment": {"appointment_id": EQ},
        "add_patient": {"name": LLM, "age": EQ, "gender": EQ, "relation": EQ},
    },
    "DawaGharApp": {
        "add_to_cart": {"medicine_id": EQ, "quantity": EQ},
        "remove_from_cart": {"medicine_id": EQ, "quantity": EQ},
        "place_order": {"address_id": EQ, "payment": EQ, "prescription_id": EQ},
        "attach_prescription": {"order_id": EQ, "prescription_id": EQ},
        "cancel_order": {"order_id": EQ},
        "set_refill_reminder": {"medicine_id": EQ, "interval_days": EQ},
        "delete_refill_reminder": {"reminder_id": EQ},
    },
}

APP_NAMES = {
    "PaySetuApp": "PaySetu",
    "RailMitraApp": "RailMitra",
    "SafarHubApp": "SafarHub",
    "KartBazaarApp": "KartBazaar",
    "StyleGaliApp": "StyleGali",
    "ThaliDashApp": "ThaliDash",
    "SehatCareApp": "SehatCare",
    "DawaGharApp": "DawaGhar",
}


def grader_entries() -> tuple[dict[str, dict[str, CheckerType]], dict[str, list[SoftCheckerType]]]:
    """Registry entries keyed by class name and, as an alias, by app name."""
    hard: dict[str, dict[str, CheckerType]] = {}
    soft: dict[str, list[SoftCheckerType]] = {}
    for class_name, tools in WRITE_TOOL_CHECKERS.items():
        for prefix in (class_name, APP_NAMES[class_name]):
            for tool, checkers in tools.items():
                key = f"{prefix}__{tool}"
                hard[key] = dict(checkers)
                if LLM in checkers.values():
                    soft[key] = [SoftCheckerType.content_checker]
    return hard, soft


def register_grader_settings() -> None:
    """Add the Bharat apps to ARE's judge registries and fix its verdict parsing. Safe to call more than once."""
    hard, soft = grader_entries()
    TOOL_ARG_CHECKER_TYPE_REGISTRY.update(hard)
    TOOL_SOFT_CHECKER_TYPE_REGISTRY.update(soft)
    restore_true_false_verdicts()


def restore_true_false_verdicts() -> None:
    """Let ARE's judge read "[[True]]" verdicts again. Safe to call more than once.

    ARE's LiteLLM and Hugging Face engines rewrite every "True"/"False" in a reply to lowercase
    (meant for the agent's JSON), but the sanity, signature, cab and tone checkers wait for the
    exact text "[[True]]". With such an engine as judge they never get a verdict, and the judge
    rejects every message to the user that is not word for word the oracle's.
    """
    if getattr(LLMChecker, "_verdicts_restored", False):
        return
    original_init = LLMChecker.__init__

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        judge = self.judge

        def judge_with_verdicts(user_prompt_args):
            response = judge(user_prompt_args)
            if response is None:
                return None
            return response.replace("[[true]]", "[[True]]").replace("[[false]]", "[[False]]")

        self.judge = judge_with_verdicts

    LLMChecker.__init__ = init
    LLMChecker._verdicts_restored = True
