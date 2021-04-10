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
from mlos.Spaces.HypergridAdapters.HierarchicalToFlatHypergridAdapter import HierarchicalToFlatHypergridAdapter


class ContinuousToPolynomialBasisHypergridAdapter(HypergridAdapter):
    """ Adds polynomial basis function features for each continuous dimension in the adaptee hypergrid using
        https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html.
        All non-continuous adaptee dimensions will be present in the target hypergrid.
        Beware: Because HierarchicalHypergrids may have NaN values for some points, these NaNs will be replaced by zeros.

        Parameters
        ----------
        degree: integer
            The degree of the polynomial features.
            Default = 2.

        interaction_only: boolean
            If true, only interaction features are produced: features that are products of at most degree distinct input features
            (so not x[1] ** 2, x[0] * x[2] ** 3, etc.).
            Default = False

        include_bias: boolean
            If True, then include a bias column, the feature in which all polynomial powers are zero
            (i.e. a column of ones - acts as an intercept term in a linear model).
            Default = True
    """

    def __init__(
            self,
            adaptee: Hypergrid,
            degree: int = 2,
            include_bias: bool = True,
            interaction_only: bool = False
    ):
        if not HypergridAdapter.is_like_simple_hypergrid(adaptee):
            raise ValueError("Adaptee must implement a Hypergrid Interface.")

        HypergridAdapter.__init__(self, name=adaptee.name, random_state=adaptee.random_state)

        self._adaptee: Hypergrid = adaptee
        self._polynomial_features_kwargs = {
            'degree': degree,
            'interaction_only': interaction_only,
            'include_bias': include_bias,
            'order': 'C'
        }
        self._target: Hypergrid = None

        if self._adaptee.is_hierarchical():
            self._adaptee = HierarchicalToFlatHypergridAdapter(adaptee=self._adaptee)

        # Record which adaptee dimensions are continuous
        self._adaptee_contains_dimensions_to_transform = False
        self._adaptee_dimension_names_to_transform = []
        for adaptee_dimension in self._adaptee.dimensions:
            if isinstance(adaptee_dimension, ContinuousDimension):
                self._adaptee_dimension_names_to_transform.append(adaptee_dimension.name)
        self._num_dimensions_to_transform = len(self._adaptee_dimension_names_to_transform)
        self._adaptee_contains_dimensions_to_transform = self._num_dimensions_to_transform > 0

        # see definition of _get_polynomial_feature_names() for usage
        self._internal_feature_name_terminal_char = '_'

        # Since sklearn PolynomialFeatures does not accept NaNs and these may appear in data frames from hierarchical hypergrids,
        # the NaNs will be replaced with an imputed (finite) value.  The following sets the value used.
        self._nan_imputed_finite_value = 0

        # instantiate sklearn's polynomial features instance
        self._polynomial_features = PolynomialFeatures(**self._polynomial_features_kwargs)
        # because the exact number of additional dimensions that will be added depends on the parameters to sklearn's PF,
        # *and* the sklearn PF instance above doesn't determine this information until after the .fit() method is called (requiring a dataframe),
        # *and* the target hypergrid can not be constructed without knowing the resulting number of continuous dimensions,
        # a trivial dataframe is constructed (all 1s) and .fit_transform() of _polynomial_features instance is called.
        trivial_continuous_dim_x = np.ones((1, self._num_dimensions_to_transform))
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

        # Add non-transformed adaptee dimensions to the target
        for adaptee_dimension in self._adaptee.dimensions:
            if adaptee_dimension.name not in self._adaptee_dimension_names_to_transform:
                self._target.add_dimension(adaptee_dimension.copy())

        if not self._adaptee_contains_dimensions_to_transform:
            return

        # add new dimensions to be created by sklearn PolynomialFeatures

        # construct target dim names using adaptee dim names and polynomial feature powers matrix
        # This logic is worked out explicitly here so we have control over the derived dimension names.
        # Currently, the code only substitutes adaptee feature names into the default feature_names produced by
        # sklearn's PolynomialFeatures .get_feature_names() method.
        poly_feature_dim_names = self._get_polynomial_feature_names()
        for i, poly_feature_name in enumerate(poly_feature_dim_names):
            ith_terms_powers = self._polynomial_features_powers[i]

            if not self._polynomial_features_kwargs['include_bias'] and ith_terms_powers.sum() == 0:
                # the constant term is skipped
                continue
            else:
                # replace adaptee dim names for poly feature name {x0_, x1_, ...} representatives
                target_dim_name = poly_feature_name
                for j, adaptee_dim_name in enumerate(self._adaptee_dimension_names_to_transform):
                    adaptee_dim_power = ith_terms_powers[j]
                    if adaptee_dim_power == 0:
                        continue
                    if adaptee_dim_power == 1:
                        poly_feature_adaptee_dim_name_standin = f'x{j}{self._internal_feature_name_terminal_char}'
                        adaptee_dim_replacement_name = adaptee_dim_name
                    else:
                        # power > 1 cases
                        poly_feature_adaptee_dim_name_standin = f'x{j}{self._internal_feature_name_terminal_char}^{adaptee_dim_power}'
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

    @property
    def polynomial_features_kwargs(self) -> dict:
        return self._polynomial_features_kwargs

    @property
    def nan_imputed_finite_value(self):
        return self._nan_imputed_finite_value

    def get_column_names_for_polynomial_features(self, degree=None):
        # column names ordered by target dimension index as this coincides with the polynomial_features.powers_ table
        sorted_by_column_index = {k: v for k, v in sorted(self._target_polynomial_feature_map.items(), key=lambda item: item[1])}
        if degree is None:
            return list(sorted_by_column_index.keys())

        dim_names = []
        for ith_terms_powers, poly_feature_name  in zip(self._polynomial_features_powers, self._get_polynomial_feature_names()):
            if ith_terms_powers.sum() == degree:
                dim_names.append(poly_feature_name)
        return dim_names

    def get_polynomial_feature_powers_table(self):
        return self._polynomial_features_powers

    def get_num_polynomial_features(self):
        return self._polynomial_features_powers.shape[0]

    def _get_polynomial_feature_names(self):
        # The default polynomial feature feature names returned from .get_feature_names() look like: ['1', 'x0', 'x1', 'x0^2', 'x0 x1', 'x1^2']
        # They are altered below by adding a terminal char so string substitutions don't confuse
        # a derived feature named 'x1 x12' with another potentially derived feature named 'x10 x124'
        replaceable_feature_names = []
        for i in range(len(self._adaptee_dimension_names_to_transform)):
            replaceable_feature_names.append(f'x{i}{self._internal_feature_name_terminal_char}')
        return self._polynomial_features.get_feature_names(replaceable_feature_names)

    def _project_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)

        # replace NaNs with zeros
        df.fillna(self._nan_imputed_finite_value, inplace=True)

        # Transform the continuous columns and add the higher order columns to the df
        # Filtering columns to transform b/c dataframes coming from hierarchical hypergrid points
        # may not contain all possible dimensions knowable from hypergrid
        x_to_transform = np.zeros((len(df.index), len(self._adaptee_dimension_names_to_transform)))
        for i, dim_name in enumerate(self._adaptee_dimension_names_to_transform):
            if dim_name in df.columns.values:
                x_to_transform[:, i] = df[dim_name]

        all_poly_features = self._polynomial_features.transform(x_to_transform)
        for target_dim_name in self._target_polynomial_feature_map:
            target_dim_index = self._target_polynomial_feature_map[target_dim_name]
            df[target_dim_name] = all_poly_features[:, target_dim_index]
        return df

    def _unproject_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)

        # unproject simply drops the monomial columns whose degree is not 1
        polynomial_feature_powers = self.get_polynomial_feature_powers_table()
        column_names_to_drop = []
        for target_dim_name, powers_table_index in self._target_polynomial_feature_map.items():
            target_powers = polynomial_feature_powers[powers_table_index]
            if target_powers.sum() == 1:
                continue
            column_names_to_drop.append(target_dim_name)
        df.drop(columns=column_names_to_drop, inplace=True)

        return df
