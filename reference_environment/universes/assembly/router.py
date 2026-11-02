"""Agree-or-escalate routing for the agent's model calls.

At every step two models are asked for the next action. When they choose the same tool with the same arguments (free
text such as a message's content is not compared: two models never word it alike), the first model's reply is used.
When they differ, or either reply has no parsable action, a fallback model answers that step instead. Every decision is
logged with token usage.

run_agent installs it in its child process when RLU_ROUTER is set and the agent's model is "router":

    RLU_ROUTER='{"models": ["fireworks_ai:<cheap A>", "fireworks_ai:<cheap B>"], "fallback": "fireworks_ai:<strong>"}'
"""

from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROUTER_MODEL = "router"
FREE_TEXT = {"content", "message", "body", "text", "note", "subject", "reply", "description"}
_DECODER = json.JSONDecoder()


def parse_action(text: str) -> dict | None:
    """The action a reply chooses, as ARE's default agent reads it: the JSON object after the last "Action:"."""
    if "Action:" not in text:
        return None
    tail = text.rsplit("Action:", 1)[1]
    start = tail.find("{")
    if start < 0:
        return None
    try:
        action, _ = _DECODER.raw_decode(tail[start:])
    except ValueError:
        return None
    return action if isinstance(action, dict) and isinstance(action.get("action"), str) else None


def _normalise(value: object) -> object:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip().lower()
    if isinstance(value, dict):
        return {key: _normalise(item) for key, item in value.items() if key not in FREE_TEXT}
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    return value


def same_action(first: dict | None, second: dict | None) -> bool:
    """Same tool and the same arguments, free-text fields aside."""
    if first is None or second is None:
        return False
    return first["action"] == second["action"] and _normalise(first.get("action_input") or {}) == _normalise(
        second.get("action_input") or {}
    )


def install(config: dict, log_path: Path) -> None:
    """Route every completion asked of ROUTER_MODEL; calls for any other model (the judge) pass through."""
    from are.simulation.agents.llm.litellm import litellm_engine

    completion = litellm_engine.completion
    (first, second), fallback = [spec.split(":", 1) for spec in config["models"]], config["fallback"].split(":", 1)
    lock = threading.Lock()
    pool = ThreadPoolExecutor(2)

    def ask(spec: list[str], kwargs: dict):
        provider, model = spec
        return completion(**{**kwargs, "model": model, "custom_llm_provider": provider})

    def log(entry: dict) -> None:
        with lock, log_path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(entry) + "\n")

    def usage(response) -> dict:
        return {"in": response.usage.prompt_tokens, "out": response.usage.completion_tokens}

    def routed_completion(*args, **kwargs):
        if kwargs.get("model") != ROUTER_MODEL:
            return completion(*args, **kwargs)
        kwargs.pop("api_base", None), kwargs.pop("api_key", None)
        replies = list(pool.map(lambda spec: ask(spec, kwargs), (first, second)))
        actions = [parse_action(reply.choices[0].message.content or "") for reply in replies]
        entry = {
            "actions": [action and action["action"] for action in actions],
            "usage": [usage(reply) for reply in replies],
        }
        if same_action(*actions):
            log({**entry, "decision": "agree"})
            return replies[0]
        answer = ask(fallback, kwargs)
        log({**entry, "decision": "fallback", "fallback_usage": usage(answer)})
        return answer

    litellm_engine.completion = routed_completion
