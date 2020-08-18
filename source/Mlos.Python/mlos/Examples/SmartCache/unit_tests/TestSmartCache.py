#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest

from mlos.Examples.SmartCache.CacheImplementations.MruCache import MruCache
from mlos.Examples.SmartCache.CacheImplementations.LruCache import LruCache
from mlos.Examples.SmartCache.CacheImplementations.CacheEntry import CacheEntry

class TestSmartCache(unittest.TestCase):
    """ Functionally tests the smart cache.

    The various implementations and parameters in the smart cache should be robust to be usable within
    the "SmartCache". This test suite is meant to ascertain they are.

    """

    @classmethod
    def setUpClass(cls) -> None:
        ...

    @classmethod
    def tearDownClass(cls) -> None:
        ...

    def setUp(self):
        ...

    def tearDown(self):
        ...

    def test_lru_cache_eviction_order(self):
        """ Tests whether a small lru cache does in fact evict entries in least recently used order. """
        lru_cache = LruCache(max_size=10)

        # Let's fill in the cache
        #
        for i in range(10):
            lru_cache.push(CacheEntry(key=i, value=str(i)))

        # Let's now continue pushing new elements into the cache, always making sure
        # that the element at n-10 has been evicted

        for i in range(10, 100):
            self.assertTrue(i - 10 in lru_cache)
            lru_cache.push(CacheEntry(key=i, value=str(i)))
            self.assertFalse(i - 10 in lru_cache)

    def test_mru_cache_eviction_order(self):
        """ Tests whether a small mru cache does in fact evict in most recently used order. """
        mru_cache = MruCache(max_size=10)

        # Let's fill in the cache
        #
        for i in range(10):
            mru_cache.push(CacheEntry(key=i, value=str(i)))

        # Let's now continue pushing new elements into the cache, always making sure that
        # all but the most recently used element persist.

        for i in range(10, 100):

            for i in range(9):
                self.assertTrue(i in mru_cache)
            mru_cache.push(CacheEntry(key=i, value=str(i)))

            for i in range(9):
                self.assertTrue(i in mru_cache)



