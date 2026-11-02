# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from functools import total_ordering
from heapq import heapify, heappop, heappush
from queue import Queue
from threading import Lock
from typing import Generic, TypeVar

T = TypeVar("T")


@total_ordering
class HeapItem(Generic[T]):
    def __init__(self, item: T, fields: list[str]):
        self.item = item
        self.fields = fields

    def __lt__(self, other):
        if isinstance(other, HeapItem):
            return self.get_tuple(self) < self.get_tuple(other)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, HeapItem):
            return self.get_tuple(self) == self.get_tuple(other)
        return NotImplemented

    def __hash__(self):
        return hash(self.get_tuple(self))

    def __repr__(self):
        return repr(self.item)

    def get_tuple(self, item: "HeapItem"):
        return tuple([getattr(item.item, f) for f in self.fields])


class PriorityQueue(Queue, Generic[T]):
    """Thread-safe priority queue with ordering based on specified fields."""

    def __init__(self, maxsize: int = 0, fields: list[str] | None = None) -> None:
        super().__init__(maxsize)
        self._init(maxsize)
        self.fields = fields
        self.lock = Lock()  # Ensure thread-safe access to self.queue

    def _init(self, maxsize):
        self.queue = []

    def _qsize(self):
        with self.lock:
            return len(self.queue)

    def _put(self, item: T):
        with self.lock:
            if self.fields is not None:
                item = HeapItem(item, self.fields)  # type: ignore
            heappush(self.queue, item)

    def _get(self) -> T:
        with self.lock:
            result = heappop(self.queue)
            if isinstance(result, HeapItem):
                return result.item
            return result

    def peek(self) -> T | None:
        with self.lock:
            result = self.queue[0] if self.queue else None
            if isinstance(result, HeapItem):
                return result.item
            return result

    def __contains__(self, item: T):
        with self.lock:
            if self.fields is not None:
                item = HeapItem(item, self.fields)  # type: ignore
            return item in self.queue

    def __len__(self):
        with self.lock:
            return len(self.queue)

    def __iter__(self):
        with self.lock:
            sorted_list = sorted(self.queue)
            if self.fields is not None:
                sorted_list = [item.item for item in sorted_list]
            return iter(sorted_list)

    def __getitem__(self, index):
        with self.lock:
            result = sorted(self.queue)[index]
            if isinstance(result, HeapItem):
                return result.item
            return result

    def __setitem__(self, index, value: T):
        with self.lock:
            if self.fields is not None:
                value = HeapItem(value, self.fields)  # type: ignore
            sorted_heap = sorted(self.queue)
            sorted_heap[index] = value
            self.queue = sorted_heap
            heapify(self.queue)

    def __delitem__(self, index):
        with self.lock:
            sorted_heap = sorted(self.queue)
            del sorted_heap[index]
            self.queue = sorted_heap
            heapify(self.queue)

    def __repr__(self):
        with self.lock:
            return repr(sorted(self.queue))

    def extend(self, items: list[T]):
        with self.lock:
            for item in items:
                self.put(item)

    def list_view(self) -> list[T]:
        with self.lock:
            return list(sorted(self.queue))
