#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

import pandas as pd

from mlos.Spaces import CategoricalDimension, ContinuousDimension, Hypergrid, Point, SimpleHypergrid
from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.OptimizerEvaluationTools.SyntheticFunctions.sample_functions import quadratic

class ThreeLevelQuadratic(ObjectiveFunctionBase):
    """ Wraps the MultilevelQuadratic to provide the interface defined in the ObjectiveFunctionBase.

    """

    _domain = SimpleHypergrid(
        name="three_level_quadratic_config",
        dimensions=[
            CategoricalDimension(name="vertex_height", values=["low", 5, 15])
        ]
    ).join(
        subgrid=SimpleHypergrid(
            name="low_quadratic_params",
            dimensions=[
                ContinuousDimension(name="x_1", min=-100, max=100),
                ContinuousDimension(name="x_2", min=-100, max=100),
            ]
        ),
        on_external_dimension=CategoricalDimension(name="vertex_height", values=["low"])
    ).join(
        subgrid=SimpleHypergrid(
            name="medium_quadratic_params",
            dimensions=[
                ContinuousDimension(name="x_1", min=-100, max=100),
                ContinuousDimension(name="x_2", min=-100, max=100),
            ]
        ),
        on_external_dimension=CategoricalDimension(name="vertex_height", values=[5])
    ).join(
        subgrid=SimpleHypergrid(
            name="high_quadratic_params",
            dimensions=[
                ContinuousDimension(name="x_1", min=-100, max=100),
                ContinuousDimension(name="x_2", min=-100, max=100),
            ]
        ),
        on_external_dimension=CategoricalDimension(name="vertex_height", values=[15])
    )

    _range = SimpleHypergrid(
        name='range',
        dimensions=[
            ContinuousDimension(name='y', min=0, max=math.inf)
        ]
    )

    _vertical_translations = {
        "low": 0,
        "medium": 5,
        "high": 15
    }

    def __init__(self, objective_function_config: Point = None):
        assert objective_function_config is None, "This function takes no configuration."
        ObjectiveFunctionBase.__init__(self, objective_function_config)

    @property
    def parameter_space(self) -> Hypergrid:
        return self._domain

    @property
    def output_space(self) -> Hypergrid:
        return self._range

    def evaluate_point(self, point):
        assert point in self._domain
        value = None
        if point.vertex_height == "low":
            value = quadratic(
                x_1=point.low_quadratic_params.x_1,
                x_2=point.low_quadratic_params.x_2
            ) + self._vertical_translations[point.vertex_height]
        elif point.vertex_height == 5:
            value = quadratic(
                x_1=point.medium_quadratic_params.x_1,
                x_2=point.medium_quadratic_params.x_2
            ) + point.vertex_height
        elif point.vertex_height == 15:
            value = quadratic(
                x_1=point.high_quadratic_params.x_1,
                x_2=point.high_quadratic_params.x_2
            ) + point.vertex_height
        else:
            raise RuntimeError(f"Unrecognized point.vertex_height value: {point.vertex_height}")

        return Point(y=value)

    def evaluate_dataframe(self, dataframe: pd.DataFrame):
        all_ys = []

        lows = dataframe[dataframe['vertex_height'] == "low"]
        if not lows.empty:
            y_for_lows = lows["low_quadratic_params.x_1"] ** 2 + lows["low_quadratic_params.x_1"] ** 2
            all_ys.append(y_for_lows)

        mids = dataframe[dataframe['vertex_height'] == 5]
        if not mids.empty:
            y_for_mids = mids["medium_quadratic_params.x_1"] ** 2 + mids["medium_quadratic_params.x_1"] ** 2
            all_ys.append(y_for_mids)

        highs = dataframe[dataframe['vertex_height'] == 15]

        if not highs.empty:
            y_for_highs = highs["high_quadratic_params.x_1"] ** 2 + highs["high_quadratic_params.x_1"] ** 2
            all_ys.append(y_for_highs)

        concatenated_ys = pd.concat(all_ys)
        ys_df = pd.DataFrame({'y': concatenated_ys})
        ys_df = ys_df.sort_index()
        return ys_df

    def get_context(self) -> Point:
        """ Returns a context value for this objective function.

        If the context changes on every invocation, this should return the latest one.
        :return:
        """
        return Point()
