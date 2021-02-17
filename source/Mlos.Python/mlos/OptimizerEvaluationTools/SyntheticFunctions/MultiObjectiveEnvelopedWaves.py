#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np
import pandas as pd
from typing import Dict

from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.OptimizerEvaluationTools.SyntheticFunctions.EnvelopedWaves import EnvelopedWaves, enveloped_waves_config_store
from mlos.Spaces.Configs import ComponentConfigStore
from mlos.Utils.KeyOrderedDict import KeyOrderedDict

from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid, Hypergrid

multi_objective_enveloped_waves_config_space = SimpleHypergrid(
    name="multi_objective_enveloped_waves_config",
    dimensions=[
        DiscreteDimension(name="num_objectives", min=1, max=10),
        ContinuousDimension(name="phase_difference", min=0, max=2 * math.pi),
        ContinuousDimension(name="period_change", min=1, max=1.2),
        CategoricalDimension(name="single_objective_function", values=[EnvelopedWaves.__name__])
    ]
).join(
    on_external_dimension=CategoricalDimension(name="single_objective_function", values=[EnvelopedWaves.__name__]),
    subgrid=enveloped_waves_config_store.parameter_space
)

multi_objective_enveloped_waves_config_store = ComponentConfigStore(
    parameter_space=multi_objective_enveloped_waves_config_space,
    default=Point(
        num_objectives=2,
        phase_difference=0.5 * math.pi,
        period_change=1.1,
        single_objective_function=EnvelopedWaves.__name__,
        enveloped_waves_config=enveloped_waves_config_store.default
    ),
    description="TODO"
)

class MultiObjectiveEnvelopedWaves(ObjectiveFunctionBase):
    """Multi-objective function with many useful properties.
    The way it works is that we pass the same parameters through 1 or more single-objective enveloped waves functions.
    One useful property is that we not only know where the optima for individual functions are (maxima of sine are easy to find),
    but we can also know and control the shape of the pareto frontier, by controlling the phase difference between the individual
    objectives. For example: a phase difference of 0, means that that the objective functions are overlaid on top of each other
    and their optima are exactly on top of each other, so the pareto frontier is a single, optimal point
    Alternatively, the phase difference of quarter-period, introduces a trade-off between the objectives where
        y0 = sin(x)
        and
        y1 = sin(x - math.pi / 2) = -cos(x)
    which yields a pareto frontier in a shape of a quarter-cirle of radius 1 (or amplitude more generally).
    Yet another option is to use a phase difference of math.pi. This yields a trade-off between the objectives where:
        y0 = sin(x)
        and
        y1 = sin(x - math.pi) = -sin(x) = -y0
    which yields a pareto frontier where a gain in one objective results in an equal loss in the other objective, so the shape
    of that frontier is a diagonal of a square with side length equal to amplitude.
    """

    def __init__(self, objective_function_config: Point = None):
        assert objective_function_config in multi_objective_enveloped_waves_config_space
        ObjectiveFunctionBase.__init__(self, objective_function_config)
        single_objective_enveloped_waves_config = objective_function_config.enveloped_waves_config
        self._individual_objectives = KeyOrderedDict(
            ordered_keys=[f"y{objective_id}" for objective_id in range(objective_function_config.num_objectives)],
            value_type=EnvelopedWaves
        )

        for objective_id in range(objective_function_config.num_objectives):
            config = single_objective_enveloped_waves_config.copy()
            config.phase_shift += objective_function_config.phase_difference * objective_id
            config.period *= objective_function_config.period_change ** objective_id

            while config.period > enveloped_waves_config_store.parameter_space["period"].max:
                config.period -= enveloped_waves_config_store.parameter_space["period"].max

            while config.phase_shift > enveloped_waves_config_store.parameter_space["phase_shift"].max:
                config.phase_shift -= enveloped_waves_config_store.parameter_space["phase_shift"].max

            self._individual_objectives[objective_id] = EnvelopedWaves(objective_function_config=config)

        self._parameter_space = self._individual_objectives[0].parameter_space
        self._output_space = SimpleHypergrid(
            name="range",
            dimensions=[
                ContinuousDimension(name=f"y{objective_id}", min=-math.inf, max=math.inf)
                for objective_id in range(objective_function_config.num_objectives)
            ]
        )

    @property
    def parameter_space(self) -> Hypergrid:
        return self._parameter_space

    @property
    def output_space(self) -> Hypergrid:
        return self._output_space

    def evaluate_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        results_df = pd.DataFrame()
        for objective_dim_name, individual_objective_function in self._individual_objectives:
            single_objective_df = individual_objective_function.evaluate_dataframe(dataframe)
            results_df[objective_dim_name] = single_objective_df['y']
        return results_df

    def get_context(self) -> Point:
        return self.objective_function_config
