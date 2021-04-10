#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np
import pytest
from mlos.Spaces import SimpleHypergrid, CategoricalDimension, ContinuousDimension, DiscreteDimension, OrdinalDimension
from mlos.OptimizerEvaluationTools.SyntheticFunctions.ThreeLevelQuadratic import ThreeLevelQuadratic
from mlos.Spaces.HypergridAdapters import ContinuousToPolynomialBasisHypergridAdapter
from mlos.Spaces.HypergridAdapters.CategoricalToOneHotEncodedHypergridAdapter import CategoricalToOneHotEncodedHypergridAdapter

class TestContinuousToPolynomialBasisHypergridAdapter:

    @classmethod
    def setup_class(cls) -> None:

        cls.simple_hypergrid = SimpleHypergrid(
            name='simple_adaptee',
            dimensions=[
                CategoricalDimension(name='categorical_mixed_types', values=['red', True, False, 5]),
                DiscreteDimension(name='one_to_ten', min=1, max=10),
                ContinuousDimension(name='z_one', min=-1, max=2),
                ContinuousDimension(name='z_two', min=-2, max=1),
                ContinuousDimension(name='z_3', min=-2, max=-1),
                OrdinalDimension(name='ordinal_mixed_types', ordered_values=[1, False, 'two'])
            ]
        )

        cls.unbalanced_hierarchical_hypergrid = SimpleHypergrid(
            name='hierarchical_adaptee',
            dimensions=[
                CategoricalDimension(name='categorical_mixed_types', values=['red', True, False, 3]),
                DiscreteDimension(name='one_to_ten', min=1, max=10),
                ContinuousDimension(name='x1', min=-1, max=1),
                ContinuousDimension(name='x2', min=-1, max=1),
                OrdinalDimension(name='ordinal_mixed_types', ordered_values=[3, False, 'two'])
            ]
        ).join(
            subgrid=SimpleHypergrid(
                name="nested_grid",
                dimensions=[
                    CategoricalDimension(name='categorical_mixed_types', values=['red', False, True, 3]),
                    DiscreteDimension(name='one_to_ten', min=1, max=10),
                    ContinuousDimension(name='x1', min=-1, max=1),
                    ContinuousDimension(name='x2', min=-1, max=1),
                    OrdinalDimension(name='ordinal_mixed_types', ordered_values=[3, 'two', False])
                ]
            ),
            on_external_dimension=CategoricalDimension("categorical_mixed_types", values=[True])
        )

        cls.balanced_hierarchical_hypergrid = ThreeLevelQuadratic().parameter_space

    @staticmethod
    def n_choose_k(n, k):
        return math.factorial(n) / math.factorial(k) / math.factorial(n - k)

    @pytest.mark.parametrize("degree", [2, 3, 5])
    @pytest.mark.parametrize("include_bias", [True, False])
    @pytest.mark.parametrize("interaction_only", [True, False])
    def test_dataframe_projection_parameterized(self, degree, interaction_only, include_bias):
        adaptee_kwargs = {'degree': degree, 'interaction_only': interaction_only, 'include_bias': include_bias}
        for adaptee in [self.simple_hypergrid,
                        self.unbalanced_hierarchical_hypergrid,
                        self.balanced_hierarchical_hypergrid]:
            print(f'running test for adaptee: {adaptee.name}')
            self._test_dataframe_projection(adaptee, adaptee_kwargs, num_random_points=10)

    def _test_dataframe_projection(self, adaptee, adapter_kwargs, num_random_points):
        num_adaptee_continuous_dims = 0
        for adaptee_dim in adaptee.dimensions:
            if isinstance(adaptee_dim, ContinuousDimension):
                num_adaptee_continuous_dims += 1

        # count the number of polynomial terms expected excluding the constant term
        if adapter_kwargs['interaction_only']:
            num_target_continuous_dims_expected = 0
            for i in range(adapter_kwargs['degree']):
                if i + 1 <= num_adaptee_continuous_dims:
                    num_target_continuous_dims_expected += self.n_choose_k(num_adaptee_continuous_dims, i+1)
        else:
            num_target_continuous_dims_expected = self.n_choose_k(adapter_kwargs['degree'] + num_adaptee_continuous_dims, num_adaptee_continuous_dims) - 1
        if adapter_kwargs['include_bias']:
            num_target_continuous_dims_expected += 1

        adapter = ContinuousToPolynomialBasisHypergridAdapter(adaptee=adaptee, **adapter_kwargs)
        num_polynomial_features = len(adapter.get_column_names_for_polynomial_features())
        assert num_polynomial_features == num_target_continuous_dims_expected

        original_df = adaptee.random_dataframe(num_samples=num_random_points)

        # test in_place=False
        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        assert id(original_df) != id(projected_df)
        assert all([target_dim_name in projected_df.columns.values for target_dim_name in adapter.get_column_names_for_polynomial_features()])

        # test values are as expected
        self._test_polynomial_feature_values_are_as_expected(adapter, projected_df)

        unprojected_df = adapter.unproject_dataframe(df=projected_df, in_place=False)
        # since NaNs can not be passed through sklearn's PolynomialFeatures transform(), they are replaced w/ 0s during projection
        # hence the unprojected data frame will have 0s where the original had NaNs.
        original_df_with_fillna_zeros = original_df.fillna(adapter.nan_imputed_finite_value)
        assert original_df_with_fillna_zeros.equals(unprojected_df)

        # test in_place=True
        projected_in_place_df = adapter.project_dataframe(original_df, in_place=True)
        assert id(original_df) == id(projected_in_place_df)
        assert projected_in_place_df.equals(projected_df)
        assert all([target_dim_name in projected_in_place_df.columns.values for target_dim_name in
                    adapter.get_column_names_for_polynomial_features()])

        # test values are as expected
        self._test_polynomial_feature_values_are_as_expected(adapter, projected_in_place_df)

        unprojected_in_place_df = adapter.unproject_dataframe(df=projected_in_place_df, in_place=True)
        assert original_df_with_fillna_zeros.equals(unprojected_in_place_df)

    @pytest.mark.parametrize("degree", [2, 3, 5])
    @pytest.mark.parametrize("interaction_only", [True, False])
    def test_point_projection_parameterized(self, degree, interaction_only):
        adaptee_kwargs = {'degree': degree, 'interaction_only': interaction_only}
        for adaptee in [self.simple_hypergrid,
                        self.unbalanced_hierarchical_hypergrid,
                        self.balanced_hierarchical_hypergrid]:
            print(f'running test for adaptee: {adaptee.name}')
            self._test_point_projection(adaptee, adaptee_kwargs, num_random_points=10)

    @staticmethod
    def _test_point_projection(adaptee, adapter_kwargs, num_random_points):
        adapter = ContinuousToPolynomialBasisHypergridAdapter(adaptee=adaptee, **adapter_kwargs)

        for _ in range(num_random_points):
            original_point = adaptee.random()
            projected_point = adapter.project_point(original_point)
            unprojected_point = adapter.unproject_point(projected_point)
            # since points from hierarchical hypergrids may lack some possible dimensions,
            # *and* this adapter's .project_dataframe() method imputes a fixed value,
            # *and* the rows at which imputation was performed are not tracked,
            # it is impossible to know if an unprojected point dimension was imputed during project,
            # the following only tests the dimensions known to exist in the original_point
            assert all([unprojected_point[original_dim] == original_point[original_dim] for original_dim in original_point.to_dict().keys()])

    @staticmethod
    def _test_polynomial_feature_values_are_as_expected(adapter, projected_df):
        # Determine if target column values contain the expected polynomial feature values
        # This is done using the PolynomialFeatures powers_ table where the rows correspond to the target features
        # and the columns to the adaptee dimensions being transformed
        target_dim_names = adapter.get_column_names_for_polynomial_features()

        for i, ith_target_dim_powers in enumerate(adapter.get_polynomial_feature_powers_table()):
            # only testing higher degree monomials since the adaptee continuous dimensions are not altered
            if ith_target_dim_powers.sum() <= 1:
                continue
            target_dim_name = target_dim_names[i]
            observed_values = projected_df[target_dim_name].to_numpy().reshape(-1, 1)

            # construct expected ith target values
            expected_values = np.ones((len(projected_df.index.values), 1))
            for j, jth_adaptee_dim_power in enumerate(ith_target_dim_powers):
                if jth_adaptee_dim_power == 0:
                    continue
                if adapter.polynomial_features_kwargs['include_bias']:
                    jth_dim_name = target_dim_names[j+1]
                else:
                    jth_dim_name = target_dim_names[j]

                input_values = projected_df[jth_dim_name].to_numpy().reshape(-1, 1)
                expected_values = expected_values * (input_values ** jth_adaptee_dim_power)

            # as the monomial degree increases, rounding errors accumulate -as one would expect
            # the threshold used for the sum of differences has been working for monomial degrees<= 5, but are known to fail
            # if epsilon is decreased or high degrees are tested
            sum_diffs = np.abs(expected_values - observed_values).sum()
            epsilon = 10 ** -5
            if sum_diffs >= epsilon:
                print('expected: ', expected_values)
                print('observed: ', observed_values)
            assert sum_diffs < epsilon

    @pytest.mark.parametrize("degree", [2, 3, 5])
    @pytest.mark.parametrize("include_bias", [True, False])
    @pytest.mark.parametrize("interaction_only", [True, False])
    @pytest.mark.parametrize("drop", ['first', None])
    @pytest.mark.parametrize("merge_all_categorical_dimensions", [True, False])
    def test_stacking_polynomial_feature_on_one_hot_encoding_parameterized(
        self,
        degree,
        include_bias,
        interaction_only,
        drop,
        merge_all_categorical_dimensions
    ):
        # The RegressionEnhancedRandomForestRegressionModel stacks polynomial feature adapter on one hot encoding adapter.
        # When the RERF code was changed to use these adapters, there was some concern about how the stacking was done.
        # This test tries to replicate the result of using the expected stacking pattern.
        for adaptee in [self.simple_hypergrid,
                        self.unbalanced_hierarchical_hypergrid,
                        self.balanced_hierarchical_hypergrid]:
            print(f'running test for adaptee: {adaptee.name}')

            one_hot_encoder_adapter = CategoricalToOneHotEncodedHypergridAdapter(
                adaptee=adaptee,
                merge_all_categorical_dimensions=merge_all_categorical_dimensions,
                drop=drop
            )

            polynomial_features_adapter = ContinuousToPolynomialBasisHypergridAdapter(
                adaptee=one_hot_encoder_adapter,
                degree=degree,
                include_bias=include_bias,
                interaction_only=interaction_only
            )

        original_df = adaptee.random_dataframe(num_samples=10)
        projected_df = polynomial_features_adapter.project_dataframe(df=original_df, in_place=True)

        # test values are as expected
        self._test_polynomial_feature_values_are_as_expected(polynomial_features_adapter, projected_df)
