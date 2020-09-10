#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np
from pandas import DataFrame
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Hypergrid, Point, SimpleHypergrid
from mlos.Spaces.HypergridAdapters.HypergridAdapter import HypergridAdapter
from mlos.Spaces.HypergridAdapters.CategoricalToDiscreteHypergridAdapter import CategoricalToDiscreteHypergridAdapter


class DiscreteToUnitContinuousHypergridAdapter(HypergridAdapter):
    """ Maps values in discrete dimensions into values in a unit continuous dimensions.

    Unit continuous all target dimensions are between 0 and 1.

    And more importantly, unmaps the continuous values back to discrete ones.

    """

    def __init__(self, adaptee: Hypergrid):
        if not HypergridAdapter.is_like_simple_hypergrid(adaptee):
            raise ValueError("Adaptee must implement a Hypergrid Interface.")
        HypergridAdapter.__init__(self, name=adaptee.name, random_state=adaptee.random_state)
        self._adaptee: Hypergrid = adaptee
        self._target: Hypergrid = None

        # Forward mapping:
        #   Key: adaptee dimension name
        #   Value: target dimension
        #
        self._adaptee_to_target_dimension_mappings = dict()

        # Reverse mapping:
        #   Key: target dimension name
        #   Value: adaptee dimension
        self._target_to_adaptee_dimension_mappings = dict()

        if any(isinstance(dimension, CategoricalDimension) for dimension in self._adaptee.dimensions):
            self._adaptee = CategoricalToDiscreteHypergridAdapter(adaptee=self._adaptee)

        # Now we need to build the target hypergrid and the mappings between adaptee and target.
        self._build_simple_hypergrid_target()


    @property
    def adaptee(self) -> Hypergrid:
        return self._adaptee

    @property
    def target(self) -> Hypergrid:
        return self._target

    def _project_point(self, point: Point) -> Point:
        projected_point = Point()
        for dim_name, original_dim_value in point:
            adaptee_dimension = self._adaptee[dim_name]
            if isinstance(adaptee_dimension, DiscreteDimension):
                # simply scale the value
                projected_point[dim_name] = (original_dim_value - adaptee_dimension.min * 1.0) / len(adaptee_dimension)
            elif isinstance(adaptee_dimension, ContinuousDimension):
                if adaptee_dimension.min == adaptee_dimension.max:
                    projected_point[dim_name] = 0
                else:
                    projected_point[dim_name] = (original_dim_value - adaptee_dimension.min * 1.0) / (adaptee_dimension.max - adaptee_dimension.min)
            else:
                raise ValueError(f"Dimension {adaptee_dimension.name} is neither Discrete nor Continuous.")
        return projected_point

    def _unproject_point(self, point: Point) -> Point:
        unprojected_point = Point()
        for dim_name, projected_dim_value in point:
            adaptee_dimension = self._adaptee[dim_name]
            if isinstance(adaptee_dimension, DiscreteDimension):
                # simply scale the value the other way
                unprojected_point[dim_name] = math.floor(projected_dim_value * len(adaptee_dimension) + adaptee_dimension.min)
            elif isinstance(adaptee_dimension, ContinuousDimension):
                unprojected_point[dim_name] = projected_dim_value * (adaptee_dimension.max - adaptee_dimension.min) + adaptee_dimension.min
            else:
                raise ValueError(f"Dimension {adaptee_dimension.name} is neither Discrete nor Continuous.")
        return unprojected_point

    def _project_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        # Basically apply the scaling for each column.
        #
        if not in_place:
            df = df.copy(deep=True)

        for adaptee_dimension in self._adaptee.dimensions:
            dim_name = adaptee_dimension.name
            if isinstance(adaptee_dimension, DiscreteDimension):
                df[dim_name] = (df[dim_name] - adaptee_dimension.min) / len(adaptee_dimension)
            elif isinstance(adaptee_dimension, ContinuousDimension):
                if adaptee_dimension.min == adaptee_dimension.max:
                    df[dim_name] = 0
                else:
                    df[dim_name] = (df[dim_name] - adaptee_dimension.min) / (adaptee_dimension.max - adaptee_dimension.min)
            else:
                raise ValueError(f"Dimension {adaptee_dimension.name} is neither Discrete nor Continuous.")
        return df

    def _unproject_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)

        for adaptee_dimension in self._adaptee.dimensions:
            dim_name = adaptee_dimension.name
            if isinstance(adaptee_dimension, DiscreteDimension):
                if df[dim_name].isnull().any():
                    df.loc[:, dim_name] = np.floor(df[dim_name] * len(adaptee_dimension) + adaptee_dimension.min)
                else:
                    # If there are no nulls, we must cast back to int64.
                    df.loc[:, dim_name] = np.floor(df[dim_name] * len(adaptee_dimension) + adaptee_dimension.min).astype(np.int64)

            elif isinstance(adaptee_dimension, ContinuousDimension):
                df.loc[:, dim_name] = df[dim_name] * (adaptee_dimension.max - adaptee_dimension.min) + adaptee_dimension.min
            else:
                raise ValueError(f"Dimension {adaptee_dimension.name} is neither Discrete nor Continuous.")
        return df

    def _build_simple_hypergrid_target(self) -> None:
        """ Builds a SimpleHypergrid target for a SimpleHypergrid adaptee.

        :return:
        """

        self._target = SimpleHypergrid(
            name=self._adaptee.name,
            dimensions=None,
            random_state=self._adaptee.random_state
        )

        # Now we iterate over all dimensions and when necessary map the CategoricalDimensions to DiscreteDimensions
        #
        for adaptee_dimension in self._adaptee.dimensions:
            if isinstance(adaptee_dimension, DiscreteDimension):
                target_dimension = ContinuousDimension(name=adaptee_dimension.name, min=0, max=1, include_max=False)
            else:
                target_dimension = ContinuousDimension(
                    name=adaptee_dimension.name,
                    min=0,
                    max=1,
                    include_min=adaptee_dimension.include_min,
                    include_max=adaptee_dimension.include_max
                )

            self._target.add_dimension(target_dimension)
            self._adaptee_to_target_dimension_mappings[adaptee_dimension.name] = target_dimension
            self._target_to_adaptee_dimension_mappings[target_dimension.name] = adaptee_dimension
