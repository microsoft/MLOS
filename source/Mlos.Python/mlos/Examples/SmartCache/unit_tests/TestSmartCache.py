#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
import random
import unittest

from mlos.Examples.SmartCache import SmartCache
from mlos.Examples.SmartCache.CacheImplementations.MruCache import MruCache
from mlos.Examples.SmartCache.CacheImplementations.LruCache import LruCache
from mlos.Examples.SmartCache.CacheImplementations.CacheEntry import CacheEntry
from mlos.Examples.SmartCache import SmartCacheWorkloadGenerator
from mlos.Mlos.SDK import mlos_globals

from mlos.Logger import  create_logger

class TestSmartCache(unittest.TestCase):
    """ Functionally tests the smart cache.

    The various implementations and parameters in the smart cache should be robust to be usable within
    the "SmartCache". This test suite is meant to ascertain they are.

    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.logger = create_logger("TestSmartCache", logging_level=logging.DEBUG)
        mlos_globals.init_mlos_global_context()

    @classmethod
    def tearDownClass(cls) -> None:
        ...

    def setUp(self):
        ...

    def tearDown(self):
        ...

    def test_lru_cache(self):

        for i in range(1, 10):
            lru_cache = LruCache(max_size=10 * i, logger=self.logger)

            for j in range(1000 * i):
                key = j % (20 * i)
                lru_cache.push(CacheEntry(key=key, value=str(j)))

    def test_smart_cache(self):
        workload_generator = SmartCacheWorkloadGenerator(logger=self.logger)
        cache = SmartCache(logger=self.logger)
        random.seed(1)
        for i in range(100):
            rand_int = random.randint(1, 1000)
            self.logger.debug(f"[{i+1}/100] rand_int = {rand_int}")
            workload_generator.fibonacci(sequence_number=rand_int, smart_cache=cache)




    def test_lru_cache_eviction_order(self):
        """ Tests whether a small lru cache does in fact evict entries in least recently used order. """
        lru_cache = LruCache(max_size=10, logger=self.logger)

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
        mru_cache = MruCache(max_size=10, logger=self.logger)

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



