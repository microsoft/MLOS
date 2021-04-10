#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from numbers import Number
import pytest

from mlos.Spaces import SimpleHypergrid, CategoricalDimension, ContinuousDimension, DiscreteDimension, OrdinalDimension
from mlos.Spaces.HypergridAdapters import CategoricalToOneHotEncodedHypergridAdapter


class TestCategoricalToOneHotEncodedHypergridAdapter:

    @classmethod
    def setup_class(cls) -> None:

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

    # Point project/unproject
    @pytest.mark.parametrize("drop", ['first', None])
    @pytest.mark.parametrize("merge_all_categorical_dimensions", [True, False])
    def test_projecting_point_from_categorical_to_one_hot_encoding_simple_hypergrid_parameterized(self, drop, merge_all_categorical_dimensions):
        for adaptee in [self.simple_hypergrid, self.hierarchical_hypergrid]:
            adapter = CategoricalToOneHotEncodedHypergridAdapter(
                adaptee=adaptee,
                drop=drop,
                merge_all_categorical_dimensions=merge_all_categorical_dimensions
            )
            test_types_are_not_categorical = [dimension.__class__ != CategoricalDimension for dimension in adapter.dimensions]
            assert all(test_types_are_not_categorical)

            self._test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(
                adaptee=adaptee,
                adapter=adapter,
                num_random_points=100
            )

    # DataFrame project/unproject tests
    @pytest.mark.parametrize("drop", ['first', None])
    @pytest.mark.parametrize("merge_all_categorical_dimensions", [True, False])
    def test_projecting_dataframe_from_flat_to_one_hot_encoded_hypergrid_parameterized(self, drop, merge_all_categorical_dimensions):
        for adaptee in [self.simple_hypergrid, self.hierarchical_hypergrid]:
            adapter = CategoricalToOneHotEncodedHypergridAdapter(
                adaptee=adaptee,
                drop=drop,
                merge_all_categorical_dimensions=merge_all_categorical_dimensions
            )
            test_types_are_not_categorical = [dimension.__class__ != CategoricalDimension for dimension in adapter.dimensions]
            assert all(test_types_are_not_categorical)

            self._test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(
                adapter=adapter,
                adaptee=adaptee,
                num_random_points=1000
            )

    # Helper functions
    @staticmethod
    def _test_projecting_dataframe_categorical_to_one_hot_encoding_point_from_adaptee(adaptee, adapter, num_random_points: int):
        original_df = adaptee.random_dataframe(num_samples=num_random_points)
        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        assert id(original_df) != id(projected_df)
        for column in adapter.get_one_hot_encoded_column_names():
            assert projected_df[column].isin([0, 1]).all()
        unprojected_df = adapter.unproject_dataframe(df=projected_df, in_place=False)
        assert original_df.equals(unprojected_df)
        assert all([expected_column_name in projected_df.columns.values
                    for expected_column_name in adapter.get_one_hot_encoded_column_names()])

        # Let's make sure that projecting in place works as expected.
        projected_in_place_df = adapter.project_dataframe(original_df, in_place=True)
        assert id(original_df) == id(projected_in_place_df)
        assert projected_in_place_df.equals(projected_df)
        assert all([expected_column_name in projected_in_place_df.columns.values
                    for expected_column_name in adapter.get_one_hot_encoded_column_names()])

        unprojected_in_place_df = adapter.unproject_dataframe(projected_in_place_df, in_place=True)
        assert id(original_df) == id(unprojected_in_place_df)
        assert unprojected_in_place_df.equals(unprojected_df[unprojected_in_place_df.columns.values])

    @staticmethod
    def _test_projecting_categorical_to_one_hot_encoding_point_from_adaptee(adaptee, adapter, num_random_points: int):
        # First make sure that none of the resulting dimensions are categorical.
        #
        assert not any(isinstance(dimension, CategoricalDimension) for dimension in adapter.dimensions)

        # Now let's make sure that we can translate a bunch of points successfully.
        #

        for _ in range(num_random_points):
            original_point = adaptee.random()
            projected_point = adapter.project_point(original_point)
            # Now let's ascertain that each coordinate in the projected point is in fact a number.
            #
            assert all(isinstance(dim_value, Number) for dim_name, dim_value in projected_point)

            # Now make sure previous categorical dimensions are not present
            #
            original_categorical_dim_names = adapter.get_original_categorical_column_names()
            assert all(original_cat_dim_name not in projected_point for original_cat_dim_name in original_categorical_dim_names)

            # Now make sure one hot encoded dimensions are 0 and 1 only
            #
            ohe_dim_names = adapter.get_one_hot_encoded_column_names()
            assert all(projected_point[dim_name] in [0, 1] for dim_name in ohe_dim_names)

            # Now let's make sure that the unprojected_point is the same as the original
            #
            unprojected_point = adapter.unproject_point(projected_point)
            assert original_point == unprojected_point
