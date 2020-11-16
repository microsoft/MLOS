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
        3. It will be able to decide whether any given point is dominated or not (needed for Monte Carlo utility functions)

    Each point will be characterized by:
        1. Configuration parameters
        2. Objective function values

    A point belongs to a pareto frontier if it is not dominated by any other point. So if two points have the exact same values
    for all objectives (but different configurations), we will consider both of them to be pareto efficient.


    """

    def __init__(
        self,
        optimization_problem: OptimizationProblem,
        features_df: pd.DataFrame,
        objectives_df: pd.DataFrame
    ):
        assert len(features_df.index) == len(objectives_df.index)
        assert all(column in optimization_problem.feature_space.dimension_names for column in features_df.columns)
        assert all(column in optimization_problem.objective_space.dimension_names for column in objectives_df.columns)

        # TODO: maybe prealloate larger arrays...
        self.optimization_problem = optimization_problem
        self.features_df = features_df
        self.objectives_df = objectives_df

    @staticmethod
    def compute_pareto(optimization_problem: OptimizationProblem, objectives_df: pd.DataFrame) -> pd.DataFrame:
        """Computes a pareto frontier for the given objectives_df.

        We do this by consecutively removing dominated points from objectives_df until none are left.


        :param optimization_problem:
        :param objectives_df:
        :return:
        """

        assert all(column in optimization_problem.objective_space.dimension_names for column in objectives_df.columns)

        # By presorting we guarantee, that all dominated points are below the currently considered point.
        #
        

