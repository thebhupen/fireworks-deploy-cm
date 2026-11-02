# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Utilities for working with iterators that can be counted.

.. py:class:: T

   Type variable representing the type of elements in the iterator.
"""

from typing import Generic, Iterator, TypeVar

#: Type variable representing the type of elements in the iterator.
T = TypeVar("T", covariant=True)


class CountableIterator(Generic[T]):
    """An iterator wrapper that provides a __len__ method.

    This class wraps an iterator and provides a __len__ method that returns the total
    number of items in the iterator, if known. This is useful for progress bars that
    need to know the total number of items in advance.

    :param iterator: The iterator to wrap
    :type iterator: Iterator[T]
    :param total_count: The total number of items in the iterator, or None if unknown
    """

    def __init__(self, iterator: Iterator[T], total_count: int | None = None):
        self.iterator = iterator
        self.total_count = total_count

    def __iter__(self) -> Iterator[T]:
        return self.iterator

    def __next__(self) -> T:
        return next(self.iterator)

    def __len__(self) -> int:
        """Return the total number of items in the iterator, if known.

        If the total count is not known, this will raise a TypeError.
        This follows Python's convention for objects that don't support len().

        :return: The total number of items in the iterator
        :raises TypeError: If the total count is not known
        """
        if self.total_count is None:
            raise TypeError("object of type 'CountableIterator' has no len()")
        return self.total_count
