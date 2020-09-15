#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from pandas import DataFrame

from mlos.Spaces import Dimension, Hypergrid, Point, SimpleHypergrid
from mlos.Spaces.HypergridAdapters.HypergridAdapter import HypergridAdapter


class HierarchicalToFlatHypergridAdapter(HypergridAdapter):
    """ Flattens a hierarchical Hypergrid object to a flat Hypergrid.

    """
    def __init__(self, adaptee: Hypergrid):
        HypergridAdapter.__init__(self, name=adaptee.name, random_state=adaptee.random_state)
        self._adaptee: Hypergrid = adaptee
        self._target: SimpleHypergrid = None
        self._forward_name_mapping = dict()
        self._backward_name_mapping = dict()

        if HypergridAdapter.is_like_simple_hypergrid(self._adaptee):
            # Need to flatten all the names
            target_dimensions = []
            for adaptee_dimension in self._adaptee.dimensions:
                target_dimension_name = Dimension.flatten_dimension_name(adaptee_dimension.name)
                self._forward_name_mapping[adaptee_dimension.name] = target_dimension_name
                self._backward_name_mapping[target_dimension_name] = adaptee_dimension.name
                target_dimension = adaptee_dimension.copy()
                target_dimension.name = target_dimension_name
                target_dimensions.append(target_dimension)

            self._target = SimpleHypergrid(
                name=self._adaptee.name,
                dimensions=target_dimensions
            )
        else:
            raise TypeError(f"Cannot build CompositeToSImpleHypergridAdapter for object of type {type(self._adaptee)}.")

    @property
    def adaptee(self) -> Hypergrid:
        return self._adaptee

    @property
    def target(self) -> Hypergrid:
        return self._target

    def _project_point(self, point: Point) -> Point:
        return point.flat_copy()

    def _unproject_point(self, point: Point) -> Point:
        unflattened_dict = {
            self._backward_name_mapping[dim_name]: value for dim_name, value in point
        }
        return Point(**unflattened_dict)

    def _project_dataframe(self, df: DataFrame, in_place: bool) -> DataFrame:
        if in_place:
            df.rename(columns=self._forward_name_mapping, inplace=True, copy=False)
            return df
        return df.rename(columns=self._forward_name_mapping, inplace=in_place, copy=not in_place)

    def _unproject_dataframe(self, df: DataFrame, in_place: bool) -> DataFrame:
        if in_place:
            # Apparently if we pass inplace=True, the rename returns None, otherwise it returns a new dataframe.
            #
            df.rename(columns=self._backward_name_mapping, inplace=True, copy=False)
            return df
        return df.rename(columns=self._backward_name_mapping)
