# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


# Re-export all utilities from the new files
# This ensures backward compatibility with code that imports from are.simulation.utils

# LLM utilities
# Context manager utilities
from are.simulation.agents.llm.llm_engine import ModelConfig
from are.simulation.utils.context_utils import conditional_context_manager, time_limit

# Iterator utilities
from are.simulation.utils.countable_iterator import CountableIterator

# Data structure utilities
from are.simulation.utils.data_utils import (
    deserialize_dynamic,
    from_dict,
    get_state_dict,
    load_state_dict,
)
from are.simulation.utils.llm_utils import (
    DEFAULT_APP_AGENT,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    build_llm,
)

# Miscellaneous utilities
from are.simulation.utils.misc import (
    add_reset,
    batched,
    get_function_name,
    helper_delay_range,
    save_jsonl,
    strip_app_name_prefix,
    truncate_string,
    uuid_hex,
)

# Serialization utilities
from are.simulation.utils.serialization import (
    EnumEncoder,
    SkippableDeepCopy,
    make_serializable,
    serialize_field,
)

# Streaming utilities
from are.simulation.utils.streaming_utils import stream_pool

# Type checking utilities
from are.simulation.utils.type_utils import check_type, is_optional_type, type_check

# For backward compatibility, ensure all symbols from the original utils.py are available
__all__ = [
    # LLM utilities
    "DEFAULT_APP_AGENT",
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "build_llm",
    "ModelConfig",
    "conditional_context_manager",
    "time_limit",
    # Serialization utilities
    "EnumEncoder",
    "SkippableDeepCopy",
    "make_serializable",
    "serialize_field",
    # Type checking utilities
    "check_type",
    "is_optional_type",
    "type_check",
    # Data structure utilities
    "deserialize_dynamic",
    "from_dict",
    "get_state_dict",
    "load_state_dict",
    # Iterator utilities
    "CountableIterator",
    # Streaming utilities
    "stream_pool",
    # Miscellaneous utilities
    "add_reset",
    "batched",
    "get_function_name",
    "helper_delay_range",
    "save_jsonl",
    "strip_app_name_prefix",
    "truncate_string",
    "uuid_hex",
]
