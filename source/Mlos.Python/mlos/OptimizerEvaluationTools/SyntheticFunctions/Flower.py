#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

import numpy as np
import pandas as pd

from mlos.Spaces import ContinuousDimension, Hypergrid, Point, SimpleHypergrid
from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase

class Flower(ObjectiveFunctionBase):
    """ Flower function exposing the ObjectiveFunctionBase interface.

    """

    _domain = SimpleHypergrid(
        name="flower",
        dimensions=[
            ContinuousDimension(name='x1', min=-100, max=100),
            ContinuousDimension(name='x2', min=-100, max=100)
        ]
    )

    _range = SimpleHypergrid(
        name='range',
        dimensions=[
            ContinuousDimension(name='y', min=-math.inf, max=math.inf)
        ]
    )

    def __init__(self, objective_function_config: Point = None):
        assert objective_function_config is None, "This function takes no configuration."
        ObjectiveFunctionBase.__init__(self, objective_function_config)

    @property
    def parameter_space(self) -> Hypergrid:
        return self._domain

    @property
    def output_space(self) -> Hypergrid:
        return self._range


    def evaluate_dataframe(self, dataframe: pd.DataFrame):
        a = 1
        b = 2
        c = 4
        x = dataframe.to_numpy()
        sum_of_squares = np.sum(x**2, axis=1)
        x_norm = np.sqrt(sum_of_squares)
        values = a * x_norm + b * np.sin(c * np.arctan2(x[:, 0], x[:, 1]))
        return pd.DataFrame({'y': values})


    def get_context(self) -> Point:
        """ Returns a context value for this objective function.

        If the context changes on every invokation, this should return the latest one.
        :return:
        """
        return Point()
