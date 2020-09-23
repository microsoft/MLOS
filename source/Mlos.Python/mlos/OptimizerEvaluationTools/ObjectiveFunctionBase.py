#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod

import pandas as pd

from mlos.Spaces import Hypergrid, Point


class ObjectiveFunctionBase(ABC):
    """ A base class defining an interface for all ObjectiveFunction classes.

    """

    @abstractmethod
    def __init__(self, objective_function_config: Point, *args, **kwargs):
        self.objective_function_config = objective_function_config

    @property
    @abstractmethod
    def parameter_space(self) -> Hypergrid:
        """Returns the hypergrid describing the parameter space for this objective function.

        :return:
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def output_space(self) -> Hypergrid:
        """Returns the hypergrid describing the output space for this objective function.

        :return:
        """
        raise NotImplementedError

    def evaluate_point(self, point: Point) -> Point:
        # If evaluate_point is not implemented in the subclass, we can make it work like so:
        #
        point_df = point.to_dataframe()
        values_df = self.evaluate_dataframe(point_df)
        values_point = Point.from_dataframe(values_df)
        return values_point

    @abstractmethod
    def evaluate_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def get_context(self) -> Point:
        """ Returns a context value for this objective function.

        If the context changes on every invokation, this should return the latest one.
        :return:
        """
        raise NotImplementedError
