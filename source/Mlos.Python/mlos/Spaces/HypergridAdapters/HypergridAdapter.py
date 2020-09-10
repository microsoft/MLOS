#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import abstractmethod
import numpy as np
from pandas import DataFrame
from mlos.Spaces import Hypergrid, Point, SimpleHypergrid


class HypergridAdapter(Hypergrid):
    """ A base class for all HypergridAdapters

    """

    @staticmethod
    def is_like_simple_hypergrid(hypergrid):
        return isinstance(hypergrid, SimpleHypergrid) or (isinstance(hypergrid, HypergridAdapter) and isinstance(hypergrid.target, SimpleHypergrid))

    @abstractmethod
    def __init__(self, name=None, random_state=None):
        Hypergrid.__init__(self, name=name, random_state=random_state)

    @property
    @abstractmethod
    def adaptee(self) -> Hypergrid:
        """Returns the adaptee hypergrid. """
        raise NotImplementedError()

    @property
    @abstractmethod
    def target(self) -> Hypergrid:
        """Returns the target hypergrid. """
        raise NotImplementedError()

    # Forward all Hypergrid APIs to self.target
    #
    def __contains__(self, item):
        if isinstance(item, Point):
            unprojected_point = self._unproject_point(item)
            return self.adaptee.__contains__(unprojected_point)
        raise NotImplementedError

    def __getitem__(self, item):
        return self.target.__getitem__(item)

    @property
    def random_state(self):
        return self.target.random_state

    @random_state.setter
    def random_state(self, value):
        self.target.random_state = value

    @property
    def dimensions(self):
        return self.target.dimensions

    def get_dimensions_for_point(self, point, return_join_dimensions=True):
        return self.target.get_dimensions_for_point(point, return_join_dimensions)

    def random(self, point=None):
        adaptee_random = self.adaptee.random(point=point)
        return self._project_point(adaptee_random)

    def is_hierarchical(self):
        return self.target.is_hierarchical()

    def join(self, subgrid, on_external_dimension):
        raise RuntimeError("Join operation is non-sensical for a HypergridAdapter.")

    def project_point(self, point: Point) -> Point:
        if isinstance(self.adaptee, HypergridAdapter):
            point = self.adaptee.project_point(point)
        return self._project_point(point)

    def unproject_point(self, point: Point) -> Point:
        point = self._unproject_point(point)
        if isinstance(self.adaptee, HypergridAdapter):
            point = self.adaptee.unproject_point(point)
        return point

    def project_dataframe(self, df: DataFrame, in_place: bool = True) -> DataFrame:
        if isinstance(self.adaptee, HypergridAdapter):
            df = self.adaptee.project_dataframe(df, in_place)
            # If the adaptee made a copy, we can do our projection in place (on that copy)
            #
            in_place = True

        # Before projecting let's make sure we have all the dimensions we need
        #
        column_names = set(df.columns.values)
        for dimension in self.adaptee.dimensions:
            if dimension.name not in column_names:
                df[dimension.name] = np.nan
        return self._project_dataframe(df, in_place)

    def unproject_dataframe(self, df: DataFrame, in_place: bool = True) -> DataFrame:
        df = self._unproject_dataframe(df, in_place)
        if isinstance(self.adaptee, HypergridAdapter):
            # If self made a copy, the adaptee can unprojecte in_place (on that copy)
            #
            df = self.adaptee.unproject_dataframe(df, in_place=True)
        return df

    def _project_point(self, point: Point) -> Point:
        """ Projects a given point from adaptee hypergrid to target hypergrid.

        If the subclass does not implement this method, we can do it automatically. The hand-written projection logic
        would likely be way more efficient, but we should also consider the programmer-time vs. cpu-time trade off.

        :param point:
        :return:
        """
        original_dataframe = point.to_dataframe()
        projected_dataframe = self.project_dataframe(original_dataframe)
        projected_point = Point.from_dataframe(projected_dataframe)
        return projected_point

    def _unproject_point(self, point: Point) -> Point:
        """ Projects a given point from target hypergrid to adaptee hypergrid.

        If the subclass does not implement this method, we can do it automatically. The hand-written projection logic
        would likely be way more efficient, but we should also consider the programmer-time vs. cpu-time trade off.

        :param point:
        :return:
        """
        original_dataframe = point.to_dataframe()
        unprojected_dataframe = self.unproject_dataframe(original_dataframe)
        unprojected_point = Point.from_dataframe(unprojected_dataframe)
        return unprojected_point

    @abstractmethod
    def _project_dataframe(self, df: DataFrame, in_place: bool) -> DataFrame:
        """ Projects a given dataframe from adaptee to target hypergrid.

        :param df:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def _unproject_dataframe(self, df: DataFrame, in_place: bool) -> DataFrame:
        """ Projects a given dataframe from target to adaptee hypergrid.

        :param df:
        :return:
        """
        raise NotImplementedError()
