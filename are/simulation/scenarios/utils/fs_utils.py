# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import random
import re


def get_random_sentence(text: str) -> str:
    sentences = re.split(r"[.!?]\s+", text)
    return random.choice(sentences)


def get_topk_words(text, k):
    """
    This function returns the top k words from a text with their number of occurrences

    Arguments:
        text (str): the text to process
        k (int): the number of words to return

    Returns:
        topk (dict[str][int]): keys are words and value is the number of occurrences
    """

    # split the text into words
    words = text.split()
    topk = {}
    for word in words:
        if word in topk:
            topk[word] += 1
        else:
            topk[word] = 1

    # sort the dictionary by value in descending order
    topk = dict(sorted(topk.items(), key=lambda item: item[1], reverse=True))

    # return the top k words
    return {k: topk[k] for k in list(topk)[:k]}
