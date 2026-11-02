# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import string
import unicodedata

from bs4 import BeautifulSoup


def extract_text_between_tags(html_content: str, tag_name: str) -> list[str]:
    """
    Extracts and returns the text content between the last occurrence of a specified HTML tag.
    :param html_content (str): The HTML content to parse.
    :param tag_name (str): The name of the tag to search for.
    :return: list[str]: The text content of the last occurrence of the specified tag, or None if the tag is not found.
    """

    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all occurrences of the specified tag
    tags = soup.find_all(tag_name)

    return [tag.get_text() for tag in tags]


def normalize_str(s: str) -> str:
    """
    Normalizes a string by converting it to lowercase, removing accents, and removing punctuation.
    """
    # Convert to lowercase
    s = s.lower()
    # Remove accents
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    # Remove punctuation
    s = s.translate(str.maketrans("", "", string.punctuation))
    return s.strip()


def normalize_arg(arg: str | None) -> str:
    """
    Normalizes an argument by converting it to a string and removing accents and punctuation.
    """
    return normalize_str(str(arg))
