#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import abstractmethod

from mlos.Examples.SmartCache.CacheImplementations.LinkedList import LinkedList, LinkedListNode
from mlos.Examples.SmartCache.CacheImplementations.CacheInterface import CacheInterface

class XruCache(CacheInterface):
    """ A base class for both LruCache and MruCache.

    The two caches have basically the same implementation, the only difference is that
    in Lru we evict from the tail of the linked-list, whereas in the Mru we evict from
    the head.

    """

    def __init__(self, max_size, logger):
        CacheInterface.__init__(self)
        assert max_size > 0
        self.logger = logger

        self._max_size = max_size
        self._dict = dict()
        self._list = LinkedList()
        self._count = 0

    def __iter__(self):
        for node in self._list:
            yield node.cache_entry

    def __len__(self):
        return len(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def get(self, key):
        if key not in self:
            return None
        node = self._dict[key]
        self._list.move_to_head(node)
        return node.cache_entry.value

    def push(self, cache_entry):
        evicted_entry = None

        if cache_entry.key in self:
            # Let's replace the key's value and bump it to the head of the list.
            node = self._dict[cache_entry.key]
            node.cache_entry = cache_entry
            self._list.move_to_head(node)
        else:
            if self._count >= self._max_size:
                evicted_entry = self.evict()

            if self._count < self._max_size:
                new_entry_node = LinkedListNode(cache_entry)
                self._dict[cache_entry.key] = new_entry_node
                self._list.insert_at_head(new_entry_node)
                self._count += 1

        return evicted_entry

    @abstractmethod
    def evict(self):
        raise NotImplementedError()
