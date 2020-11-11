#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from numbers import Number
import math

from mlos.Spaces import SimpleHypergrid, CategoricalDimension, ContinuousDimension, DiscreteDimension, OrdinalDimension
from mlos.OptimizerEvaluationTools.SyntheticFunctions.ThreeLevelQuadratic import ThreeLevelQuadratic
from mlos.Spaces.HypergridAdapters import ContinuousToPolynomialBasisHypergridAdapter


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

    ## simple_hypergrid tests
    def test_simple_hypergrid_degree_two_all_terms(self):
        adapter_kwargs = {
            'degree': 2,
            'interaction_only': False
        }
        self._test_dataframe_projection(adaptee=self.simple_hypergrid, adapter_kwargs=adapter_kwargs, num_random_points=10)

    def test_simple_hypergrid_degree_three_all_terms(self):
        adapter_kwargs = {
            'degree': 3,
            'interaction_only': False
        }
        self._test_dataframe_projection(adaptee=self.simple_hypergrid, adapter_kwargs=adapter_kwargs, num_random_points=10)

    def test_simple_hypergrid_degree_two_no_interaction_terms(self):
        adapter_kwargs = {
            'degree': 2,
            'interaction_only': True
        }
        self._test_dataframe_projection(adaptee=self.simple_hypergrid, adapter_kwargs=adapter_kwargs, num_random_points=10)

    # unbalanced_hierarchical_hypergrid tests
    def test_unbalanced_hierarchical_hypergrid_degree_two_all_terms(self):
        adapter_kwargs = {
            'degree': 2,
            'interaction_only': False
        }

        self._test_dataframe_projection(adaptee=self.unbalanced_hierarchical_hypergrid, adapter_kwargs=adapter_kwargs, num_random_points=10)

    def test_unbalanced_hierarchical_hypergrid_degree_three_all_terms(self):
        adapter_kwargs = {
            'degree': 3,
            'interaction_only': False
        }

        self._test_dataframe_projection(adaptee=self.unbalanced_hierarchical_hypergrid, adapter_kwargs=adapter_kwargs, num_random_points=10)

    # balanced_hierarchical_hypergrid_tests
    def test_balanced_hierarchical_hypergrid_degree_two_all_terms(self):
        adapter_kwargs = {
            'degree': 2,
            'interaction_only': False
        }

        self._test_dataframe_projection(adaptee=self.balanced_hierarchical_hypergrid, adapter_kwargs=adapter_kwargs, num_random_points=10)

    def test_balanced_hierarchical_hypergrid_degree_three_all_terms(self):
        adapter_kwargs = {
            'degree': 3,
            'interaction_only': False
        }

        self._test_dataframe_projection(adaptee=self.balanced_hierarchical_hypergrid, adapter_kwargs=adapter_kwargs, num_random_points=10)

    def _test_dataframe_projection(self, adaptee, adapter_kwargs, num_random_points):
        num_continuous_dims = 0
        for adaptee_dim in adaptee.dimensions:
            if isinstance(adaptee_dim, ContinuousDimension):
                num_continuous_dims += 1

        # count the number of polynomial terms expected excluding the constant term
        num_continuous_dims_expected = self.n_choose_k(adapter_kwargs['degree'] + num_continuous_dims, num_continuous_dims) - 1

        adapter = ContinuousToPolynomialBasisHypergridAdapter(adaptee=adaptee, **adapter_kwargs)
        num_polynomial_features = len(adapter.get_column_names_for_polynomial_features())
        assert num_polynomial_features == num_continuous_dims_expected

        original_df = adaptee.random_dataframe(num_samples=num_random_points)

        # test in_place=False
        projected_df = adapter.project_dataframe(df=original_df, in_place=False)
        assert id(original_df) != id(projected_df)
        assert all([target_dim_name in projected_df.columns.values for target_dim_name in adapter.get_column_names_for_polynomial_features()])

        # test in_place=True
        projected_in_place_df = adapter.project_dataframe(original_df, in_place=True)
        assert id(original_df) == id(projected_in_place_df)
        assert projected_in_place_df.equals(projected_df)
        assert all([target_dim_name in projected_in_place_df.columns.values for target_dim_name in
                    adapter.get_column_names_for_polynomial_features()])
