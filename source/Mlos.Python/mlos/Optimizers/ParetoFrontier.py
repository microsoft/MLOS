#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd
from mlos.Optimizers.OptimizationProblem import OptimizationProblem


class ParetoFrontier:
    """Maintains a set of non-dominated configurations.

    This class will have several pieces of functionality:
        1. It will be able to construct and maintain a pareto frontier from a set of observations for one or more objectives.
        2. It will be able to update the frontier upon receiving a new observation.
        3. It will be able to decide whether any given point is dominated or not (needed for Monte Carlo utility functions).

    Each point will be characterized by:
        1. Configuration parameters
        2. Objective function values
        3. Possibly context values

    A point belongs to a pareto frontier if it is not dominated by any other point. So if two points have the exact same values
    for all objectives (but possibly different configurations), we will consider both of them to be pareto efficient.


    """

    def __init__(
            self,
            optimization_problem: OptimizationProblem,
            features_df: pd.DataFrame,
            objectives_df: pd.DataFrame
    ):
        assert len(features_df.index) == len(objectives_df.index)
        if features_df is not None:
            assert all(column in optimization_problem.feature_space.dimension_names for column in features_df.columns)

        if objectives_df is not None:
            assert all(column in optimization_problem.objective_space.dimension_names for column in objectives_df.columns)

        self.optimization_problem = optimization_problem
        self.features_df = features_df
        self.objectives_df = objectives_df

    @staticmethod
    def compute_pareto(optimization_problem: OptimizationProblem, objectives_df: pd.DataFrame) -> pd.DataFrame:
        """Computes a pareto frontier for the given objectives_df (including weak-pareto-optimal points).

        We do this by consecutively removing points on the interior of the pareto frontier from objectives_df until none are left.

        We retain the points that fall onto the frontier line, for the following reasons:
            1. The code is more efficient.
            2. If they were jiggled only a little bit outwards they would be included.
            3. In real life we expect it to be an extremely rare occurrence.

        We retain duplicated points because they could be due to different configurations.

        :param optimization_problem:
        :param objectives_df:
        :return:
        """

        assert all(column in optimization_problem.objective_space.dimension_names for column in objectives_df.columns)

        # Let's copy it, since we are going to mess it up.
        #
        pareto_df = objectives_df.copy(deep=True)

        # First, let's turn it into a maximization problem, by flipping the sign of all objectives that are to be minimized.
        #
        for objective in optimization_problem.objectives:
            if objective.minimize:
                pareto_df[objective.name] = -pareto_df[objective.name]

        # By presorting we guarantee, that all dominated points are below the currently considered point.
        #
        pareto_df.sort_values(
            by=[objective.name for objective in optimization_problem.objectives],
            ascending=False, # We want the maxima up top.
            inplace=True,
            na_position='last', # TODO: figure out what to do with NaNs.
            ignore_index=False
        )

        current_row_index = 0
        while current_row_index < len(pareto_df.index):
            non_dominated = (pareto_df >= pareto_df.iloc[current_row_index]).any(axis=1)
            pareto_df = pareto_df[non_dominated]
            current_row_index += 1

        # Let's unflip the signs
        #
        for objective in optimization_problem.objectives:
            if objective.minimize:
                pareto_df[objective.name] = -pareto_df[objective.name]

        return pareto_df


    @staticmethod
    def is_dominated(objectives_df, pareto_df) -> pd.Series:
        """For each row in objectives_df checks if the row is dominated by any of the rows in pareto_df.

        :param objectives_df:
        :param pareto_df:
        :return:
        """
        is_dominated = pd.Series([False for i in range(len(objectives_df.index))], index=objectives_df.index)
        for idx, pareto_row in pareto_df.iterrows():
            is_dominated_by_this_pareto_point = (objectives_df < pareto_row).all(axis=1)
            is_dominated = is_dominated | is_dominated_by_this_pareto_point
        return is_dominated
