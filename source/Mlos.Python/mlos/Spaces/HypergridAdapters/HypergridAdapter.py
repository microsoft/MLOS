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
            untranslated_point = self._untranslate_point(item)
            return self.adaptee.__contains__(untranslated_point)
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

    def get_dimensions_for_point(self, point, external_dimensions=True):
        return self.target.get_dimensions_for_point(point, external_dimensions)

    def random(self, point=None):
        adaptee_random = self.adaptee.random(point=point)
        return self._translate_point(adaptee_random)

    def is_hierarchical(self):
        return self.target.is_hierarchical()

    def join(self, subgrid, on_external_dimension):
        raise RuntimeError("Join operation is non-sensical for a HypergridAdapter.")

    def translate_point(self, point: Point) -> Point:
        if isinstance(self.adaptee, HypergridAdapter):
            point = self.adaptee.translate_point(point)
        return self._translate_point(point)

    def untranslate_point(self, point: Point) -> Point:
        point = self._untranslate_point(point)
        if isinstance(self.adaptee, HypergridAdapter):
            point = self.adaptee.untranslate_point(point)
        return point

    def translate_dataframe(self, df: DataFrame, in_place: bool = True) -> DataFrame:
        if isinstance(self.adaptee, HypergridAdapter):
            df = self.adaptee.translate_dataframe(df, in_place)
            # If the adaptee made a copy, we can do our translation in place (on that copy)
            #
            in_place = True

        # Before translating let's make sure we have all the dimensions we need
        #
        column_names = set(df.columns.values)
        for dimension in self.adaptee.dimensions:
            if dimension.name not in column_names:
                df[dimension.name] = np.nan
        return self._translate_dataframe(df, in_place)

    def untranslate_dataframe(self, df: DataFrame, in_place: bool = True) -> DataFrame:
        df = self._untranslate_dataframe(df, in_place)
        if isinstance(self.adaptee, HypergridAdapter):
            # If self made a copy, the adaptee can untranslate in_place (on that copy)
            #
            df = self.adaptee.untranslate_dataframe(df, in_place=True)
        return df

    @abstractmethod
    def _translate_point(self, point: Point) -> Point:
        """ Translates a given point from adaptee hypergrid to target hypergrid.

        :param point:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def _untranslate_point(self, point: Point) -> Point:
        """ Translates a given point from target hypergrid to adaptee hypergrid.

        :param point:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def _translate_dataframe(self, df: DataFrame, in_place: bool) -> DataFrame:
        """ Translates a given dataframe from adaptee to target hypergrid.

        :param df:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def _untranslate_dataframe(self, df: DataFrame, in_place: bool) -> DataFrame:
        """ Translates a given dataframe from target to adaptee hypergrid.

        :param df:
        :return:
        """
        raise NotImplementedError()
