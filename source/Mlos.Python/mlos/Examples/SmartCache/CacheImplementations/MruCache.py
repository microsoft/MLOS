#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Examples.SmartCache.CacheImplementations.XruCache import XruCache
from mlos.Spaces import DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

mru_cache_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name='mru_cache_config',
        dimensions=[DiscreteDimension('cache_size', min=1, max=2 ** 12)]
    ),
    default=Point(cache_size=10)
)

class MruCache(XruCache):
    """ An implementation of a Most Recently Used (MRU) cache.

    Supposedly this type of cache works well in case of:
    1) Random accesses
    2) Cycling through the dataset that cannot fit in the cache

    The idea being that the longer something has been in the cache, the higher the probability
    that it will be used again (at least in case of 2).

    """

    def __init__(self, max_size, logger):
        XruCache.__init__(self, max_size=max_size, logger=logger)

    def evict(self):
        removed_node = self._list.remove_at_head()
        evicted_entry = removed_node.cache_entry
        del self._dict[removed_node.cache_entry.key]
        self._count -= 1
        return evicted_entry
