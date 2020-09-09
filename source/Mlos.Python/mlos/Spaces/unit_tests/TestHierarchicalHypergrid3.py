#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random
import unittest

from mlos.Spaces import CategoricalDimension, Dimension, DiscreteDimension, OrdinalDimension, Point, SimpleHypergrid

class TestHierarchicalHypergrid3(unittest.TestCase):
    """ Tests the join on external dimension in hypergrids.

    In particular:
    * Hypergrid.join(subgrid, on_external_dimension=SomeDimension(...)) should:
        * Check if the dimension.name contains a subgrid name:
            * if yes - drop the prefix and call dimension_subgrid.join(subgrid, on_external_dimension)
            * otherwise we are joining here so:
                * if not dimension.intersects(self[dimension.name]): return self
                * self.joined_subgrids_by_pivot_dimension[dimension.name] = JoinedHypergrid(dimension, subgrid)

    * Randomly generating points from the supergrid should generate points from the newly joined subgrid
    * Point containment should work
    * Hypergrid containment should work (eventually)

    """

    def setUp(self):

        self.cache_param_space = SimpleHypergrid(
            name='cache_param_space',
            dimensions=[
                CategoricalDimension(name='cache_implementation_name', values=['lru_cache', 'associative_cache'])
            ]
        )

        self.lru_cache_param_space = SimpleHypergrid(
            name='lru_cache_config',
            dimensions=[
                DiscreteDimension(name='size', min=1, max=2**20),
                OrdinalDimension(name='color', ordered_values=['green', 'orange', 'red'])
            ]
        )


        self.associative_cache_implementation_root_param_space = SimpleHypergrid(
            name='associative_cache_config',
            dimensions=[
                CategoricalDimension(name='hash_function_name', values=['mod_prime_hash_function', 'lowest_bits']),
                CategoricalDimension(name='bucket_implementation', values=['single_value', 'binary_search_tree', 'linked_list'])
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


        self.associative_cache_implementation_param_space = self.associative_cache_implementation_root_param_space.join(
            subgrid=self.mod_prime_hash_function_param_space,
            on_external_dimension=CategoricalDimension(name='hash_function_name', values=['mod_prime_hash_function'])
        ).join(
            subgrid=self.lowest_bits_param_space,
            on_external_dimension=CategoricalDimension(name='hash_function_name', values='lowest_bits')
        ).join(
            subgrid=self.binary_search_tree_param_space,
            on_external_dimension=CategoricalDimension(name='bucket_implementation', values=['binary_search_tree'])
        )

        self.cache_param_space = self.cache_param_space.join(
            subgrid=self.lru_cache_param_space,
            on_external_dimension=CategoricalDimension(name='cache_implementation_name', values=['lru_cache'])
        ).join(
            subgrid=self.associative_cache_implementation_param_space,
            on_external_dimension=CategoricalDimension(name='cache_implementation_name', values=['associative_cache'])
        ).join(
            subgrid=self.linked_list_param_space,
            on_external_dimension=CategoricalDimension(name='associative_cache_config.bucket_implementation', values=['linked_list'])
        )

    def test_external_dimension_join(self):
        for _ in range(10):
            print("################################################")
            random_config = self.cache_param_space.random()
            for param_name, value in random_config:
                print(param_name, value)
            print(random_config in self.cache_param_space)
        print("################################################")

