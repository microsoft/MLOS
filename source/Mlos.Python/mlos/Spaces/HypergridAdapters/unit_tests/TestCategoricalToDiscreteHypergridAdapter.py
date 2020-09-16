#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from numbers import Number
import unittest

import pandas as pd

from mlos.Spaces import SimpleHypergrid, CategoricalDimension, ContinuousDimension, DiscreteDimension, OrdinalDimension
from mlos.Spaces.HypergridAdapters import CategoricalToDiscreteHypergridAdapter, DiscreteToUnitContinuousHypergridAdapter,\
    HierarchicalToFlatHypergridAdapter

class TestCategoricalToDiscreteHypergridAdapter(unittest.TestCase):

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

    def test_projecting_point_from_categorical_to_discrete_simple_hypergrid(self):
        """ Tests if we can successfully execute all HypergridAdapters on a simple hypergrid.

        :return:
        """
        adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self.simple_hypergrid)
        self._test_projecting_categorical_to_discrete_point_from_adaptee(adaptee=self.simple_hypergrid, adapter=adapter)

    def test_projecting_point_to_unit_continuous_hypergrid(self):
        hypergrdis_and_adapters = [
            (self.simple_hypergrid, DiscreteToUnitContinuousHypergridAdapter(adaptee=self.simple_hypergrid)),
            (self.hierarchical_hypergrid, DiscreteToUnitContinuousHypergridAdapter(adaptee=self.hierarchical_hypergrid))
        ]
        for hypergrid, adapter in hypergrdis_and_adapters:
            for _ in range(1000):
                original_point = hypergrid.random()
                projected_point = adapter.project_point(original_point)
                self.assertTrue(all(isinstance(dim_value, float) and 0 <= dim_value <= 1 for _, dim_value in projected_point))
                self.assertTrue(projected_point in adapter)
                unprojected_point = adapter.unproject_point(projected_point)
                self.assertTrue(original_point == unprojected_point)
                self.assertTrue(unprojected_point in hypergrid)

    def test_projecting_dataframe_from_flat_to_unit_continuous_hypergrid(self):
        adapter = DiscreteToUnitContinuousHypergridAdapter(adaptee=self.simple_hypergrid)
        original_df = self.simple_hypergrid.random_dataframe(num_samples=1000)
        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        self.assertTrue(id(original_df) != id(projected_df))
        for column in projected_df.columns:
            self.assertTrue(projected_df[column].between(0, 1).all())
        unprojected_df = adapter.unproject_dataframe(df=projected_df, in_place=False)
        self.assertTrue(original_df.equals(unprojected_df))

        # Let's make sure that projecting in place works as expected.
        projected_in_place_df = adapter.project_dataframe(original_df)
        self.assertTrue(id(original_df) == id(projected_in_place_df))
        self.assertTrue(projected_in_place_df.equals(projected_df))
        unprojected_in_place_df = adapter.unproject_dataframe(projected_in_place_df)
        self.assertTrue(id(original_df) == id(unprojected_in_place_df))
        self.assertTrue(unprojected_in_place_df.equals(unprojected_df))

    def test_projecting_dataframe_from_hierarchical_to_unit_continuous_hypergrid(self):
        adapter = DiscreteToUnitContinuousHypergridAdapter(adaptee=self.hierarchical_hypergrid)
        original_df = self.hierarchical_hypergrid.random_dataframe(num_samples=1000)
        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        self.assertTrue(id(original_df) != id(projected_df))
        for column in projected_df.columns:
            self.assertTrue(projected_df[column].dropna().between(0, 1).all())
        unprojected_df = adapter.unproject_dataframe(df=projected_df, in_place=False)
        self.assertTrue(original_df.equals(unprojected_df))

        # Let's make sure that projecting in place works as expected.
        projected_in_place_df = adapter.project_dataframe(original_df)
        self.assertTrue(id(original_df) == id(projected_in_place_df))
        self.assertTrue(projected_in_place_df.equals(projected_df))
        unprojected_in_place_df = adapter.unproject_dataframe(projected_in_place_df)
        self.assertTrue(id(original_df) == id(unprojected_in_place_df))
        self.assertTrue(unprojected_in_place_df.equals(unprojected_df))


    def test_projecting_dataframe_from_categorical_to_discrete_simple_hypergrid(self):
        adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self.simple_hypergrid)
        original_df = self.simple_hypergrid.random_dataframe(num_samples=10000)
        projected_df = adapter.project_dataframe(original_df, in_place=False)
        # Let's make sure we have a deep copy.
        #
        self.assertTrue(id(original_df) != id(projected_df)) # Make sure that a deep copy was made.
        self.assertFalse(original_df.equals(projected_df))

        # TODO: assert projected df only has numbers
        # Let's copy the projected_df before testing if all is numeric - the test might change the data.
        copied_df = projected_df.copy(deep=True)
        columns = copied_df.columns.values.tolist()
        for column in columns:
            # For each column let's validate that it contains only numerics. We'll do this by coercing all values to numerics.
            # If such coercion fails, it produces a null value, so we can validate that there are no nulls in the output.
            self.assertTrue(pd.to_numeric(copied_df[column], errors='coerce').notnull().all())

        # To make sure the check above is capable of failing, let's try the same trick on the input where we know there are non-numeric values
        #
        copied_original_df = original_df.copy(deep=True)
        self.assertFalse(pd.to_numeric(copied_original_df['categorical_mixed_types'], errors='coerce').notnull().all())


        unprojected_df = adapter.unproject_dataframe(projected_df, in_place=False)
        self.assertTrue(id(original_df) != id(unprojected_df))
        self.assertTrue(original_df.equals(unprojected_df))

        # Let's make sure that projecting in place works as expected.
        projected_in_place_df = adapter.project_dataframe(original_df)
        self.assertTrue(id(original_df) == id(projected_in_place_df))
        self.assertTrue(projected_in_place_df.equals(projected_df))
        unprojected_in_place_df = adapter.unproject_dataframe(projected_in_place_df)
        self.assertTrue(id(original_df) == id(unprojected_in_place_df))
        self.assertTrue(unprojected_in_place_df.equals(unprojected_df))

    def test_projecting_point_from_hierarchical_categorical_to_discrete_hypergrid(self):
        # This used to raise, but now it's handled internally so let's make sure it doesn't raise anymore.
        hierarchical_adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self.hierarchical_hypergrid)
        self._test_projecting_categorical_to_discrete_point_from_adaptee(adaptee=self.hierarchical_hypergrid, adapter=hierarchical_adapter)

    def _test_projecting_categorical_to_discrete_point_from_adaptee(self, adaptee, adapter):
        # First make sure that none of the resulting dimensions are categorical.
        #
        self.assertFalse(any(isinstance(dimension, CategoricalDimension) for dimension in adapter.dimensions))

        # Now let's make sure that we can tranlate a bunch of points successfully.
        #
        for _ in range(1000):
            original_point = adaptee.random()
            projected_point = adapter.project_point(original_point)
            # Now let's ascertain that each coordinate in the projected point is in fact a number.
            #
            self.assertTrue(all(isinstance(dim_value, Number) for dim_name, dim_value in projected_point))

            # Now let's make sure that the unprojected_point is the same as the original
            #
            unprojected_point = adapter.unproject_point(projected_point)
            self.assertTrue(original_point == unprojected_point)

    def test_projecting_point_from_simple_to_simple_hypergrid(self):
        adapter = HierarchicalToFlatHypergridAdapter(adaptee=self.simple_hypergrid)
        self.assertTrue(isinstance(adapter.target, SimpleHypergrid))
        for _ in range(1000):
            original_point = self.simple_hypergrid.random()
            projected_point = adapter.project_point(original_point)
            for dim_name, value in projected_point:
                self.assertFalse("." in dim_name)
            self.assertTrue(original_point == projected_point) # No projection for SimpleHypergrid-to-SimpleHypergrid adapters.
            unprojected_point = adapter.unproject_point(projected_point)
            self.assertTrue(unprojected_point in self.simple_hypergrid)
            self.assertTrue(original_point == unprojected_point)

    def test_projecting_point_from_hierarchical_to_flat_hypergrid(self):
        adapter = HierarchicalToFlatHypergridAdapter(adaptee=self.hierarchical_hypergrid)
        self.assertTrue(isinstance(adapter.target, SimpleHypergrid))
        for _ in range(1000):
            original_point = self.hierarchical_hypergrid.random()
            projected_point = adapter.project_point(original_point)

            if original_point.categorical_mixed_types is True:
                self.assertFalse(projected_point == original_point)
            else:
                self.assertTrue(projected_point == original_point)

            for dim_name, value in projected_point:
                self.assertFalse("." in dim_name)
            unprojected_point = adapter.unproject_point(projected_point)
            self.assertTrue(unprojected_point in self.hierarchical_hypergrid)
            self.assertTrue(unprojected_point == original_point)

    def test_projecting_dataframe_from_hierarchical_to_flat_hypergrid(self):
        adapter = HierarchicalToFlatHypergridAdapter(adaptee=self.hierarchical_hypergrid)
        original_df = self.hierarchical_hypergrid.random_dataframe(num_samples=1000)

        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        self.assertTrue(id(original_df) != id(projected_df))
        self.assertFalse(original_df.equals(projected_df))
        columns = projected_df.columns.values.tolist()
        for column in columns:
            self.assertFalse("." in column)

        unprojected_df = adapter.unproject_dataframe(df=projected_df, in_place=False)
        self.assertTrue(id(projected_df) != id(unprojected_df))
        self.assertTrue(original_df.equals(unprojected_df))

    def test_projecting_point_from_categorical_hierachical_to_discrete_flat_hypergrid(self):
        """ Exercises the stacking functionality.

        This is a major use case for our models.

        :return:
        """
        first_adapter = HierarchicalToFlatHypergridAdapter(adaptee=self.hierarchical_hypergrid)
        adapter = CategoricalToDiscreteHypergridAdapter(adaptee=first_adapter)
        self.assertFalse(any(isinstance(dimension, CategoricalDimension) for dimension in adapter.dimensions))
        self.assertFalse(any("." in dimension.name for dimension in adapter.dimensions))

        for _ in range(1000):
            original_point = self.hierarchical_hypergrid.random()
            projected_point = adapter.project_point(original_point)

            self.assertTrue(all(isinstance(dim_value, Number) for dim_name, dim_value in projected_point))
            self.assertFalse(any("." in dim_name for dim_name, value in projected_point))
            self.assertFalse(projected_point == original_point)

            unprojected_point = adapter.unproject_point(projected_point)
            self.assertTrue(unprojected_point in self.hierarchical_hypergrid)
            self.assertTrue(original_point == unprojected_point)

    def test_projecting_dataframe_from_categorical_hierarchical_to_discrete_flat_hypergrid(self):
        adapter = CategoricalToDiscreteHypergridAdapter(
            adaptee=HierarchicalToFlatHypergridAdapter(
                adaptee=self.hierarchical_hypergrid
            )
        )
        self.assertFalse(any(isinstance(dimension, CategoricalDimension) for dimension in adapter.dimensions))
        self.assertFalse(any("." in dimension.name for dimension in adapter.dimensions))

        original_df = self.hierarchical_hypergrid.random_dataframe(num_samples=10000)
        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        unprojected_df = adapter.unproject_dataframe(df=projected_df, in_place=False)
        self.assertTrue(original_df.equals(unprojected_df))







