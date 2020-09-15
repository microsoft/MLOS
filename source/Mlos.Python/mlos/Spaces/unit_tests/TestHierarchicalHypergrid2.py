#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random
import unittest

from mlos.Spaces import CategoricalDimension, Dimension, DiscreteDimension, OrdinalDimension, Point, SimpleHypergrid

class TestHierarchicalHypergrid2(unittest.TestCase):
    """ Tests the improved implementation of the Hypergrids.

    In particular:
    * SimpleHypergrid.join() should attach to the root hypergrid if possible
    * SimpleHypergrids that are hierarchical implement a hierarchical namespace, where a coordinate within
        each subgrid is prefixed with the name of that subgrid:

    """

    def setUp(self):

        self.lru_cache_param_space = SimpleHypergrid(
            name='lru_cache_config',
            dimensions=[
                DiscreteDimension(name='size', min=1, max=2**20),
                OrdinalDimension(name='color', ordered_values=['green', 'orange', 'red'])
            ]
        )

        self.mod_prime_hash_function_param_space = SimpleHypergrid(
            name='mod_prime_hash_function',
            dimensions=[
                OrdinalDimension(name='prime', ordered_values=[1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59])
            ]
        )

        self.lowest_bits_param_space = SimpleHypergrid(
            name='lowest_bits',
            dimensions=[
                DiscreteDimension(name='num_bits', min=1, max=64)
            ]
        )

        self.binary_search_tree_param_space = SimpleHypergrid(
            name='binary_search_tree',
            dimensions=[
                DiscreteDimension(name='max_depth', min=1, max=2**10)
            ]
        )

        self.linked_list_param_space = SimpleHypergrid(
            name='linked_list',
            dimensions=[
                DiscreteDimension(name='max_length', min=1, max=2**10)
            ]
        )

        self.associative_cache_implementation_param_space = SimpleHypergrid(
            name='associative_cache_config',
            dimensions=[
                CategoricalDimension(name='hash_function_name', values=['mod_prime_hash_function', 'lowest_bits']),
                CategoricalDimension(name='bucket_implementation', values=['single_value', 'binary_search_tree', 'linked_list'])
            ]
        ).join(
            subgrid=self.mod_prime_hash_function_param_space,
            on_external_dimension=CategoricalDimension(name='hash_function_name', values=['mod_prime_hash_function'])
        ).join(
            subgrid=self.lowest_bits_param_space,
            on_external_dimension=CategoricalDimension(name='hash_function_name', values=['lowest_bits'])
        ).join(
            subgrid=self.binary_search_tree_param_space,
            on_external_dimension=CategoricalDimension(name='bucket_implementation', values=['binary_search_tree'])
        ).join(
            subgrid=self.linked_list_param_space,
            on_external_dimension=CategoricalDimension(name='bucket_implementation', values=['linked_list'])
        )

        self.cache_param_space = SimpleHypergrid(
            name='cache_param_space',
            dimensions=[
                CategoricalDimension(name='cache_implementation_name', values=['lru_cache', 'associative_cache'])
            ]
        ).join(
            subgrid=self.lru_cache_param_space,
            on_external_dimension=CategoricalDimension(name='cache_implementation_name', values=['lru_cache'])
        ).join(
            subgrid=self.associative_cache_implementation_param_space,
            on_external_dimension=CategoricalDimension(name='cache_implementation_name', values=['associative_cache'])
        )

    def test_efficient_join(self):
        """ Tests if the join efficiently flattens the tree of hypergrids.

        :return:
        """
        self.assertTrue(self.cache_param_space.name == 'cache_param_space')

        subgrids_joined_on_cache_implementation_name_dimension = set(joined_subgrid.subgrid for joined_subgrid in self.cache_param_space.joined_subgrids_by_pivot_dimension['cache_implementation_name'])
        self.assertTrue(self.lru_cache_param_space in subgrids_joined_on_cache_implementation_name_dimension)
        self.assertTrue(self.associative_cache_implementation_param_space in subgrids_joined_on_cache_implementation_name_dimension)

        subgrids_joined_on_hash_function_name_dimension = set(guest_subgrid.subgrid for guest_subgrid in self.associative_cache_implementation_param_space.joined_subgrids_by_pivot_dimension['hash_function_name'])
        self.assertTrue(self.mod_prime_hash_function_param_space in subgrids_joined_on_hash_function_name_dimension)
        self.assertTrue(self.lowest_bits_param_space in subgrids_joined_on_hash_function_name_dimension)

        subgrids_joined_on_bucket_implementation_dimension = set(guest_subgrid.subgrid for guest_subgrid in self.associative_cache_implementation_param_space.joined_subgrids_by_pivot_dimension['bucket_implementation'])
        self.assertTrue(self.binary_search_tree_param_space in subgrids_joined_on_bucket_implementation_dimension)
        self.assertTrue(self.linked_list_param_space in subgrids_joined_on_bucket_implementation_dimension)

    def test_name_flattening(self):
        num_tests = 1000

        for i in range(num_tests):
            random_config = self.cache_param_space.random()

            flat_dimensions = []
            for dimension_name, value in random_config:
                original_dimension = self.cache_param_space[dimension_name]
                flat_dimension = original_dimension.copy()
                flat_dimension.name = Dimension.flatten_dimension_name(dimension_name)
                flat_dimensions.append(flat_dimension)

            # Let's create a flat hypergrid that contains that random_config
            flat_cache_param_space = SimpleHypergrid(
                name=f"Flat{self.cache_param_space.name}",
                dimensions=flat_dimensions
            )

            flat_random_config = random_config.flat_copy()
            self.assertTrue(flat_random_config in flat_cache_param_space)

            # let's try another random config
            another_random_config = self.cache_param_space.random()
            flattened_config = another_random_config.flat_copy()
            try:
                if flattened_config in flat_cache_param_space:
                    ...
                self.assertTrue(True)
            except:
                self.assertTrue(False)

    def test_that_getitem_returns_subgrid(self):
        """ Tests if we can use the __getitem__ operator to retrieve a subgrid.

        :return:
        """
        lru_cache_param_space = self.cache_param_space['lru_cache_config']
        for _ in range(1000):
            self.assertTrue(lru_cache_param_space.random() in self.lru_cache_param_space)
            self.assertTrue(self.lru_cache_param_space.random() in lru_cache_param_space)

    def test_that_getitem_returns_dimensions(self):
        """ Tests if we can use the __getitem__ operator to retrieve a dimension.

        :return:
        """
        cache_implementation_dimension = self.cache_param_space["cache_implementation_name"]
        self.assertTrue(cache_implementation_dimension ==CategoricalDimension(name='cache_implementation_name', values=['lru_cache', 'associative_cache']))
        num_bits_dimension = self.cache_param_space["associative_cache_config"]["lowest_bits"]["num_bits"]
        self.assertTrue(num_bits_dimension == self.lowest_bits_param_space["num_bits"])

    def test_getitem_throws(self):
        with self.assertRaises(KeyError):
            self.cache_param_space["non_existent_dimension"]

    def test_that_collision_throws(self):
        """ Test that if we try to join on a subgrid that has the same name as an existing dimension, we throw.

        This is because the __getitem__ can return either a dimension or a subgrid, so their names cannot collide.

        :return:
        """
        with self.assertRaises(ValueError):
            SimpleHypergrid(
                name="collisions",
                dimensions=[
                    CategoricalDimension(name="associative_cache_config", values=[True, False]),
                    CategoricalDimension(name='cache_implementation_name', values=['lru_cache', 'associative_cache'])
                ]
            ).join(
                subgrid=self.associative_cache_implementation_param_space,
                on_external_dimension=CategoricalDimension(name='cache_implementation_name', values=['associative_cache'])
            )



