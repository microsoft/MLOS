#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np
from pandas import DataFrame
from sklearn.preprocessing import PolynomialFeatures
from mlos.Spaces import ContinuousDimension, Hypergrid, SimpleHypergrid
from mlos.Spaces.HypergridAdapters.HypergridAdapter import HypergridAdapter


class ContinuousToPolynomialBasisHypergridAdapter(HypergridAdapter):
    """ Adds polynomial basis function features for each continuous dimension in the adaptee hypergrid using
        https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html.

        Parameters
        ----------
        degree: integer
            The degree of the polynomial features.
            Default = 2.

        interaction_only: boolean
            If true, only interaction features are produced: features that are products of at most degree distinct input features
            (so not x[1] ** 2, x[0] * x[2] ** 3, etc.).
            Default = False

    """

    def __init__(
            self,
            adaptee: Hypergrid,
            degree: int = 2,
            interaction_only: bool = False
    ):
        if not HypergridAdapter.is_like_simple_hypergrid(adaptee):
            raise ValueError("Adaptee must implement a Hypergrid Interface.")

        HypergridAdapter.__init__(self, name=adaptee.name, random_state=adaptee.random_state)

        self._adaptee: Hypergrid = adaptee
        self._polynomial_features_kwargs = {
            'degree': degree,
            'interaction_only': interaction_only,
            'include_bias': True,
            'order': 'C'
        }
        self._target: Hypergrid = None

        # Record which adaptee dimensions are continuous
        self._adaptee_contains_dimensions_to_transform = False
        self._adaptee_dimension_names_to_transform = []
        for adaptee_dimension in self._adaptee.dimensions:
            if isinstance(adaptee_dimension, ContinuousDimension):
                self._adaptee_dimension_names_to_transform.append(adaptee_dimension.name)
        self._num_dimensions_to_transform = len(self._adaptee_dimension_names_to_transform)
        self._adaptee_contains_dimensions_to_transform = self._num_dimensions_to_transform > 0

        # instantiate sklearn's polynomial features instance
        self._polynomial_features = PolynomialFeatures(**self._polynomial_features_kwargs)
        # because the exact number of additional dimensions that will be added depends on the parameters to sklearn's PF,
        # *and* the sklearn PF instance above doesn't determine this information until after the .fit() method is called (requiring a dataframe),
        # *and* the target hypergrid can not be constructed without knowing the resulting number of continuous dimensions,
        # a trivial dataframe is constructed (all 1s) and .fit_transform() of _polynomial_features instance is called.
        trivial_continuous_dim_x = np.array(np.ones((1, self._num_dimensions_to_transform))).reshape(1, -1)
        trivial_polynomial_features_y = self._polynomial_features.fit_transform(trivial_continuous_dim_x)
        self._polynomial_features_powers = self._polynomial_features.powers_
        self._num_polynomial_basis_dimensions_in_target = trivial_polynomial_features_y.shape[1]
        self._target_polynomial_feature_map = {}  # keys are target dimension names, values are index in features
        self._build_simple_hypergrid_target()

    def _build_simple_hypergrid_target(self) -> None:
        self._target = SimpleHypergrid(
            name=self._adaptee.name,
            dimensions=None,
            random_state=self._adaptee.random_state
        )

        # since linear terms will always be included in the polynomial basis functions, add all dimensions
        for adaptee_dimension in self._adaptee.dimensions:
            self._target.add_dimension(adaptee_dimension.copy())

        if not self._adaptee_contains_dimensions_to_transform:
            return

        # add new dimensions to be created by sklearn PolynomialFeatures

        # construct target dim names using adaptee dim names and polynomial feature powers matrix
        # The polynomial feature "feature names" look like: ['1', 'x0', 'x1', 'x0^2', 'x0 x1', 'x1^2']
        # and this is independent of the adaptee dimension names (since the sklearn class doesn't take the x feature names as inputs).
        poly_feature_dim_names = self._polynomial_features.get_feature_names().copy()

        for i, poly_feature_name in enumerate(poly_feature_dim_names):
            ith_terms_powers = self._polynomial_features_powers[i]

            if ith_terms_powers.sum() <= 1:
                # the constant term is skipped and the linear terms are already included in _target
                continue
            else:
                # replace adaptee dim names for poly feature name {x0, x1, ...} representatives
                target_dim_name = poly_feature_name
                for j, adaptee_dim_name in enumerate(self._adaptee_dimension_names_to_transform):
                    adaptee_dim_power = ith_terms_powers[j]
                    if adaptee_dim_power == 0:
                        continue
                    if adaptee_dim_power == 1:
                        poly_feature_adaptee_dim_name_standin = f'x{j}'
                        adaptee_dim_replacement_name = adaptee_dim_name
                    else:
                        # power > 1 cases
                        poly_feature_adaptee_dim_name_standin = f'x{j}^{adaptee_dim_power}'
                        adaptee_dim_replacement_name = f'{adaptee_dim_name}^{adaptee_dim_power}'

                    target_dim_name = target_dim_name.replace(poly_feature_adaptee_dim_name_standin, adaptee_dim_replacement_name)
            # add target dimension
            # min and max are placed at -Inf and +Inf since .random() on the target hypergrid is generated on the original
            # hypergrid and passed through the adapters.
            self._target.add_dimension(
                ContinuousDimension(name=target_dim_name, min=-math.inf, max=math.inf)
            )
            self._target_polynomial_feature_map[target_dim_name] = i

    @property
    def adaptee(self) -> Hypergrid:
        return self._adaptee

    @property
    def target(self) -> Hypergrid:
        return self._target

    def get_column_names_for_polynomial_features(self):
        return list(set.union(set(self._adaptee_dimension_names_to_transform), set(self._target_polynomial_feature_map.keys())))

    def get_polynomial_feature_powers_table(self):
        return self._polynomial_features_powers

    def _project_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)

        # replace NaNs with zeros
        df.fillna(0, inplace=True)

        # transform the continuous columns and add the higher order columns to the df
        x_to_transform = np.array(df[self._adaptee_dimension_names_to_transform].to_numpy())
        all_poly_features = self._polynomial_features.transform(x_to_transform)
        for i, target_dim_name in enumerate(self._target_polynomial_feature_map):
            df[target_dim_name] = all_poly_features[:, i]
        return df

    def _unproject_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)
        print(df.columns.values)
        # unproject simply drops the higher degree polynomial feature columns
        df.drop(columns=self._target_polynomial_feature_map.keys(), inplace=True)
        return df
