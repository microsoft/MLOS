#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from pandas import DataFrame
from mlos.Spaces import CategoricalDimension, DiscreteDimension, Hypergrid, Point, SimpleHypergrid
from mlos.Spaces.HypergridAdapters.HypergridAdapter import HypergridAdapter
from mlos.Spaces.HypergridAdapters.HierarchicalToFlatHypergridAdapter import HierarchicalToFlatHypergridAdapter


class CategoricalToDiscreteHypergridAdapter(HypergridAdapter):
    """ Maps values in categorical dimensions into values in discrete dimensions.

    """

    def __init__(self, adaptee: Hypergrid):
        if not HypergridAdapter.is_like_simple_hypergrid(adaptee):
            raise ValueError("Adaptee must implement a Hypergrid Interface.")

        HypergridAdapter.__init__(self, name=adaptee.name, random_state=adaptee.random_state)
        self._adaptee: Hypergrid = adaptee
        self._target: Hypergrid = None

        # Forward mapping:
        #   Key: dimension name
        #   Value: a dictionary mapping adaptee values to target values
        #
        self._adaptee_to_target_dimension_mappings = dict()

        # Reverse mapping:
        #   Key: dimension name
        #   Value: a dictionary mapping target values to adaptee values
        self._target_to_adaptee_dimension_mappings = dict()

        if self._adaptee.is_hierarchical():
            self._adaptee = HierarchicalToFlatHypergridAdapter(adaptee=self._adaptee)

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
            forward_mapping = self._adaptee_to_target_dimension_mappings.get(dim_name, None)
            if forward_mapping is None:
                projected_point[dim_name] = original_dim_value
            else:
                projected_point[dim_name] = forward_mapping[original_dim_value]
        return projected_point

    def _unproject_point(self, point: Point) -> Point:
        unprojected_point = Point()
        for dim_name, projected_dim_value in point:
            backward_mapping = self._target_to_adaptee_dimension_mappings.get(dim_name, None)
            if backward_mapping is None:
                unprojected_point[dim_name] = projected_dim_value
            else:
                unprojected_point[dim_name] = backward_mapping[projected_dim_value]
        return unprojected_point

    def _project_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        # For each dimension that has a forward mapping, apply the mapping to the corresponding column.
        #
        if not in_place:
            df = df.copy(deep=True)
        for dim_name, forward_mapping in self._adaptee_to_target_dimension_mappings.items():
            if dim_name not in df.columns:
                continue
            df[dim_name] = df[dim_name].apply(lambda original_value: forward_mapping.get(original_value, original_value))  # pylint: disable=cell-var-from-loop
        return df

    def _unproject_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)
        for dim_name, backward_mapping in self._target_to_adaptee_dimension_mappings.items():
            if dim_name not in df.columns:
                continue
            df[dim_name] = df[dim_name].apply(lambda original_value: backward_mapping.get(original_value, original_value))  # pylint: disable=cell-var-from-loop
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
            if not isinstance(adaptee_dimension, CategoricalDimension):
                self._target.add_dimension(adaptee_dimension.copy())
            else:
                target_dimension = self._map_categorical_dimension(adaptee_dimension)
                self._target.add_dimension(target_dimension)

    def _map_categorical_dimension(self, adaptee_dimension: CategoricalDimension) -> DiscreteDimension:
        """ Projects a categorical dimension into a discrete dimension and persists the mappings.

        :param adaptee_dimension:
        :return:
        """
        forward_mapping = {}
        backward_mapping = {}
        for i, value in enumerate(adaptee_dimension):
            forward_mapping[value] = i
            backward_mapping[i] = value

        self._adaptee_to_target_dimension_mappings[adaptee_dimension.name] = forward_mapping
        self._target_to_adaptee_dimension_mappings[adaptee_dimension.name] = backward_mapping
        target_dimension = DiscreteDimension(
            name=adaptee_dimension.name,
            min=0,
            max=len(adaptee_dimension) - 1
        )
        return target_dimension
