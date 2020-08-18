#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Examples.SmartCache.CacheImplementations.XruCache import XruCache
from mlos.Spaces import DiscreteDimension, Point, SimpleHypergrid

class LruCacheConfig:
    CONFIG_SPACE = SimpleHypergrid(
        name='lru_cache_config',
        dimensions=[
            DiscreteDimension('cache_size', min=1, max=2 ** 10)
        ]
    )

    DEFAULT = Point(
        cache_size=10
    )

class LruCache(XruCache):
    """ An implementation of a Least Recently Used cache.

    We maintain a dictionary and a linked list both pointing to the same cache entry.
    Whenever an entry is touched (and when it is first inserted) it gets moved to the
    head of the linked list (in O(1) time). Whenever we try to push a new entry into
    a full cache, we expel the entry that's at the tail of the list (since it is the
    least recently used one).

    """

    def __init__(self, max_size):
        XruCache.__init__(self, max_size=max_size)

    def evict(self):
        removed_node = self._list.remove_at_tail()
        evicted_entry = removed_node.cache_entry
        del self._dict[removed_node.cache_entry.key]
        self._count -= 1
        return evicted_entry
