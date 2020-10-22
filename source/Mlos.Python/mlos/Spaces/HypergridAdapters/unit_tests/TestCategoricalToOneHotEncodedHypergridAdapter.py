#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from numbers import Number

import unittest

from mlos.Spaces import SimpleHypergrid, CategoricalDimension, ContinuousDimension, DiscreteDimension, OrdinalDimension
from mlos.Spaces.HypergridAdapters import CategoricalToOneHotEncodedHypergridAdapter


class TestCategoricalToOneHotEncodedHypergridAdapter(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:

        cls.simple_hypergrid = SimpleHypergrid(
            name='simple_adaptee',
            dimensions=[
                CategoricalDimension(name='categorical_mixed_types', values=['red', True, False, 5]),
                DiscreteDimension(name='one_to_ten', min=1, max=10),
                ContinuousDimension(name='zero_to_one', min=0, max=1),
                OrdinalDimension(name='ordinal_mixed_types', ordered_values=[1, False, 'two'])
            ]
        )

        cls.hierarchical_hypergrid = SimpleHypergrid(
            name='hierarchical_adaptee',
            dimensions=[
                CategoricalDimension(name='categorical_mixed_types', values=['red', True, False, 3]),
                DiscreteDimension(name='one_to_ten', min=1, max=10),
                ContinuousDimension(name='zero_to_one', min=0, max=1),
                OrdinalDimension(name='ordinal_mixed_types', ordered_values=[3, False, 'two'])
            ]
        ).join(
            subgrid=SimpleHypergrid(
                name="nested_grid",
                dimensions=[
                    CategoricalDimension(name='categorical_mixed_types', values=['red', False, True, 3]),
                    DiscreteDimension(name='one_to_ten', min=1, max=10),
                    ContinuousDimension(name='zero_to_one', min=0, max=1),
                    OrdinalDimension(name='ordinal_mixed_types', ordered_values=[3, 'two', False])
                ]
            ),
            on_external_dimension=CategoricalDimension("categorical_mixed_types", values=[True])
        )

    ## Point project/unproject
    # Simple Hypergrid tests
    def test_projecting_point_from_categorical_to_one_hot_encoding_simple_hypergrid(self):
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.simple_hypergrid)
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.simple_hypergrid, adapter=adapter, num_random_points=500)

    def test_projecting_point_from_categorical_to_one_hot_encoding_drop_first_simple_hypergrid(self):
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.simple_hypergrid, drop='first')
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.simple_hypergrid, adapter=adapter, num_random_points=500)

    def test_projecting_point_from_categorical_to_one_hot_encoding_cross_product_simple_hypergrid(self):
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.simple_hypergrid, merge_all_categorical_dimensions=True)
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.simple_hypergrid, adapter=adapter, num_random_points=500)

    def test_projecting_point_from_categorical_to_one_hot_encoding_cross_product_drop_first_simple_hypergrid(self):
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.simple_hypergrid, merge_all_categorical_dimensions=True, drop='first')
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.simple_hypergrid, adapter=adapter, num_random_points=500)

    # Hierarchical Hypergrid tests
    def test_projecting_point_from_hierarchical_categorical_to_one_hot_encoding_hypergrid(self):
        hierarchical_adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.hierarchical_hypergrid)
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.hierarchical_hypergrid,
                                                                                 adapter=hierarchical_adapter,
                                                                                 num_random_points=500)

    def test_projecting_point_from_hierarchical_categorical_to_one_hot_encoding_drop_first_hypergrid(self):
        hierarchical_adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.hierarchical_hypergrid, drop='first')
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.hierarchical_hypergrid,
                                                                                 adapter=hierarchical_adapter,
                                                                                 num_random_points=500)

    def test_projecting_point_from_hierarchical_categorical_to_one_hot_encoding_cross_product_hypergrid(self):
        hierarchical_adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.hierarchical_hypergrid, merge_all_categorical_dimensions=True)
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.hierarchical_hypergrid,
                                                                                 adapter=hierarchical_adapter,
                                                                                 num_random_points=100)

    def test_projecting_point_from_hierarchical_categorical_to_one_hot_encoding_cross_product_drop_first_hypergrid(self):
        hierarchical_adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=self.hierarchical_hypergrid,
                                                                          merge_all_categorical_dimensions=True,
                                                                          drop='first')
        self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee=self.hierarchical_hypergrid,
                                                                                 adapter=hierarchical_adapter,
                                                                                 num_random_points=100)

    ## DataFrame project/unproject tests
    # Simple Hypergrid tests
    def test_projecting_dataframe_from_flat_to_one_hot_encoded_hypergrid(self):
        adaptee = self.simple_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee)
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    def test_projecting_dataframe_from_flat_to_one_hot_encoded_drop_first_hypergrid(self):
        adaptee = self.simple_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee, drop='first')
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    def test_projecting_dataframe_from_flat_to_one_hot_encoded_cross_product_hypergrid(self):
        adaptee = self.simple_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee, merge_all_categorical_dimensions=True)
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    def test_projecting_dataframe_from_flat_to_one_hot_encoded_cross_product_drop_first_hypergrid(self):
        adaptee = self.simple_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee, merge_all_categorical_dimensions=True, drop='first')
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    # Hierarchical Hypergrid tests
    def test_projecting_dataframe_from_hierarchical_to_one_hot_encoding_hypergrid(self):
        adaptee = self.hierarchical_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee)
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    def test_projecting_dataframe_from_hierarchical_to_one_hot_encoding_drop_first_hypergrid(self):
        adaptee = self.hierarchical_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee, drop='first')
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    def test_projecting_dataframe_from_hierarchical_to_one_hot_encoding_cross_product_hypergrid(self):
        adaptee = self.hierarchical_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee, merge_all_categorical_dimensions=True)
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    def test_projecting_dataframe_from_hierarchical_to_one_hot_encoding_cross_product_drop_first_hypergrid(self):
        adaptee = self.hierarchical_hypergrid
        adapter = CategoricalToOneHotEncodedHypergridAdapter(adaptee=adaptee, merge_all_categorical_dimensions=True, drop='first')
        self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adapter=adapter, adaptee=adaptee, num_random_points=1000)

    # Helper functions
    def _test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(self, adaptee, adapter, num_random_points: int):
        original_df = adaptee.random_dataframe(num_samples=num_random_points)
        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        self.assertTrue(id(original_df) != id(projected_df))
        for column in adapter.get_one_hot_encoded_column_names():
            self.assertTrue(projected_df[column].isin([0, 1]).all())
        unprojected_df = adapter.unproject_dataframe(df=projected_df, in_place=False)
        self.assertTrue(original_df.equals(unprojected_df))

        # Let's make sure that projecting in place works as expected.
        projected_in_place_df = adapter.project_dataframe(original_df, in_place=True)
        self.assertTrue(id(original_df) == id(projected_in_place_df))
        self.assertTrue(projected_in_place_df.equals(projected_df))
        unprojected_in_place_df = adapter.unproject_dataframe(projected_in_place_df, in_place=True)
        self.assertTrue(id(original_df) == id(unprojected_in_place_df))
        self.assertTrue(unprojected_in_place_df.equals(unprojected_df[unprojected_in_place_df.columns.values]))

    def _test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(self, adaptee, adapter, num_random_points: int):
        # First make sure that none of the resulting dimensions are categorical.
        #
        self.assertFalse(any(isinstance(dimension, CategoricalDimension) for dimension in adapter.dimensions))

        # Now let's make sure that we can translate a bunch of points successfully.
        #

        for _ in range(num_random_points):
            original_point = adaptee.random()
            projected_point = adapter.project_point(original_point)
            # Now let's ascertain that each coordinate in the projected point is in fact a number.
            #
            self.assertTrue(all(isinstance(dim_value, Number) for dim_name, dim_value in projected_point))

            # Now make sure previous categorical dimensions are not present
            #
            original_categorical_dim_names = adapter.get_original_categorical_column_names()
            self.assertTrue(all(original_cat_dim_name not in projected_point for original_cat_dim_name in original_categorical_dim_names))

            # Now make sure one hot encoded dimensions are 0 and 1 only
            #
            ohe_dim_names = adapter.get_one_hot_encoded_column_names()
            self.assertTrue(all(projected_point[dim_name] in [0, 1] for dim_name in ohe_dim_names))

            # Now let's make sure that the unprojected_point is the same as the original
            #
            unprojected_point = adapter.unproject_point(projected_point)
            self.assertTrue(original_point == unprojected_point)
