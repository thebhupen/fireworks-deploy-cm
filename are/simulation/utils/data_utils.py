# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Type, TypeVar, get_args, get_origin, get_type_hints

from are.simulation.utils.type_utils import is_optional_type

T = TypeVar("T")


def get_state_dict(instance, fields_list: list[str]) -> dict[str, Any]:
    """
    Extract a dictionary of field values from an instance.

    :param instance: The object to extract fields from
    :param fields_list: List of field names to extract
    :type fields_list: list[str]
    :return: Dictionary mapping field names to their serialized values
    :rtype: dict[str, Any]
    """
    result = {}
    for field in fields_list:
        try:
            value = getattr(instance, field)
        except AttributeError:
            value = None
        result[field] = serialize_field(value)
    return result


def serialize_field(value: Any) -> Any:
    """
    Serialize a field value to a JSON-compatible format.

    This function handles dataclasses, Enums, lists, and dictionaries by converting
    them to their serializable equivalents.

    :param value: The value to serialize
    :type value: Any
    :return: The serialized value
    :rtype: Any
    """
    if is_dataclass(value):
        from are.simulation.utils.serialization import (
            serialize_field as serialize_field_impl,
        )

        return serialize_field_impl(value)
    elif isinstance(value, Enum):
        return value.value
    elif isinstance(value, list):
        return [serialize_field(item) for item in value]
    elif isinstance(value, dict):
        return {k: serialize_field(v) for k, v in value.items()}
    else:
        return value


def load_state_dict(instance, fields_list: list[str], data: dict[str, Any]):
    """
    Load field values from a dictionary into an instance.

    :param instance: The object to load fields into
    :param fields_list: List of field names to load
    :type fields_list: list[str]
    :param data: Dictionary mapping field names to their values
    :type data: dict[str, Any]
    :return: The updated instance
    :raises ValueError: If the instance is not a dataclass or if a field is missing
    """
    if not is_dataclass(instance):
        raise ValueError(
            f"{instance} is not a dataclass ! Only dataclasses are supported for now"
        )
    all_types = instance.__class__.__annotations__  # type: ignore
    for field in fields_list:
        if field not in all_types:
            raise ValueError(
                f"Field {field} is missing from {instance} - only found {list(all_types.keys())}"
            )
        field_type = all_types[field]
        if field not in data:
            raise ValueError(
                f"Field {field} is missing from data - only found {list(data.keys())}"
            )

        value = deserialize_dynamic(data[field], field_type)
        setattr(instance, field, value)

    return instance


TDataclass = TypeVar("TDataclass")


def from_dict(cls_or_instance: Type[TDataclass] | Any, data: dict) -> TDataclass:
    """
    Convert a dictionary into a dataclass instance.

    This function recursively converts dictionaries into dataclass instances,
    handling nested dataclasses, Enums, and Optional fields.

    :param cls: The dataclass type to create
    :param data: The dictionary containing field values
    :return: An instance of the dataclass
    :raises TypeError: If cls is not a dataclass
    """
    # If cls_or_instance is an instance, get its class
    cls = (
        cls_or_instance if isinstance(cls_or_instance, type) else type(cls_or_instance)
    )
    if not is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass.")

    field_types = get_type_hints(cls)  # Get the type hints of the dataclass fields
    init_values = {}

    for field in fields(cls):  # Iterate over dataclass fields
        field_name = field.name
        field_type = field_types[field_name]
        field_value = data.get(field_name)

        # Handle nested dataclasses
        if is_dataclass(field_type) and field_value is not None:
            init_values[field_name] = from_dict(field_type, field_value)

        # Handle Enums
        elif isinstance(field_type, type) and issubclass(field_type, Enum):
            if field_value is not None:
                init_values[field_name] = field_type[
                    field_value.upper()
                ]  # Case-insensitive enum lookup

        # Handle Optional fields
        elif is_optional_type(field_type):
            if field_value is not None:
                actual_type = get_args(field_type)[
                    0
                ]  # Get the actual type inside Optional
                if is_dataclass(actual_type):
                    init_values[field_name] = from_dict(actual_type, field_value)
                elif get_origin(actual_type) is list:
                    init_values[field_name] = deserialize_dynamic(
                        field_value, actual_type
                    )
                elif get_origin(actual_type) is dict:
                    init_values[field_name] = deserialize_dynamic(
                        field_value, actual_type
                    )
                else:
                    init_values[field_name] = actual_type(field_value)

        elif get_origin(field_type) is list:
            if field_value is not None:
                init_values[field_name] = deserialize_dynamic(
                    field_value,
                    field_type,  # type: ignore
                )

        # Handle normal fields
        else:
            init_values[field_name] = field_value

    return cls(**init_values)  # type: ignore


def deserialize_dynamic(
    data: Any,
    data_type: Type[T],
    skip_errors: bool = False,
) -> T:
    """
    Recursively deserialize data into the specified type.

    This function handles dataclasses, lists, dictionaries, and primitive types.

    :param data: The data to deserialize
    :type data: Any
    :param data_type: The target type to deserialize into
    :type data_type: Type[T]
    :param skip_errors: Whether to skip errors and return None instead
    :type skip_errors: bool
    :return: The deserialized data
    :rtype: T
    """
    import logging

    logger = logging.getLogger(__name__)

    # Check if the type is a dataclass
    if hasattr(data_type, "__dataclass_fields__"):
        # Deserialize into a dataclass
        try:
            if isinstance(data, dict):
                return from_dict(data_type, data)
            else:
                if skip_errors:
                    logger.error(
                        f"ERROR in deserializing data: expected dict, got {type(data)}",
                        "data",
                        data,
                        "type",
                        data_type,
                    )
                    return None  # type: ignore
                else:
                    raise TypeError(f"Expected dict, got {type(data)}")
        except Exception as e:
            if skip_errors:
                logger.error(
                    "ERROR in deserializing data", e, "data", data, "type", data_type
                )
                return None  # type: ignore
            else:
                raise e

    # Check if the type is a list
    if get_origin(data_type) is list:
        item_type = get_args(data_type)[0]
        if isinstance(data, (list, tuple)):
            return [deserialize_dynamic(item, item_type) for item in data]  # type: ignore
        else:
            if skip_errors:
                logger.error(
                    f"ERROR in deserializing data: expected list, got {type(data)}",
                    "data",
                    data,
                    "type",
                    data_type,
                )
                return []  # type: ignore
            else:
                raise TypeError(f"Expected list, got {type(data)}")

    # Check if the type is a dictionary
    if get_origin(data_type) is dict:
        key_type, value_type = get_args(data_type)
        if isinstance(data, dict):
            return {  # type: ignore
                deserialize_dynamic(k, key_type): deserialize_dynamic(v, value_type)
                for k, v in data.items()
            }
        else:
            if skip_errors:
                logger.error(
                    f"ERROR in deserializing data: expected dict, got {type(data)}",
                    "data",
                    data,
                    "type",
                    data_type,
                )
                return {}  # type: ignore
            else:
                raise TypeError(f"Expected dict, got {type(data)}")

    # If it's a primitive type, return it directly
    return data  # type: ignore
