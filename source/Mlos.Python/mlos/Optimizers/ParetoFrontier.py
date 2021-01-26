#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np
import pandas as pd
from scipy.stats import norm

from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Tracer import trace
from mlos.Utils.KeyOrderedDict import KeyOrderedDict

class ParetoVolumeEsimator:
    """Contains all information required to compute a confidence interval on the pareto volume.

    Note that the dimensionality analysis for this volume is meaningless. Each objective carries
    its own units, and multiplying them together is meaningless.

    Pareto volume estimate can be used to monitor the growth of the pareto frontier over time.

    """

    def __init__(
        self,
        num_random_points: int,
        num_dominated_points: int,
        objectives_maxima: KeyOrderedDict
    ):
        assert 0 <= num_dominated_points <= num_random_points
        assert len(objectives_maxima) > 0
        self.num_random_points = num_random_points
        self.num_dominated_points = num_dominated_points
        self.objectives_maxima = objectives_maxima
        self.sample_proportion_of_dominated_points = (1.0 * num_dominated_points) / num_random_points

    def get_two_sided_confidence_interval_on_pareto_volume(self, alpha=0.01):
        z_score = norm.ppf(1 - alpha / 2.0)
        p_hat = self.sample_proportion_of_dominated_points
        ci_radius = z_score * math.sqrt(p_hat * (1 - p_hat) / self.num_random_points)
        lower_bound_on_proportion = p_hat - ci_radius
        upper_bound_on_proportion = p_hat + ci_radius

        total_volume_of_enclosing_parallelotope = 1.0
        for objective, objective_maximum in self.objectives_maxima:
            total_volume_of_enclosing_parallelotope *= objective_maximum

        total_volume_of_enclosing_parallelotope = abs(total_volume_of_enclosing_parallelotope)

        lower_bound_on_pareto_volume = lower_bound_on_proportion * total_volume_of_enclosing_parallelotope
        upper_bound_on_pareto_volume = upper_bound_on_proportion * total_volume_of_enclosing_parallelotope
        return lower_bound_on_pareto_volume, upper_bound_on_pareto_volume





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

    def __init__(self, optimization_problem: OptimizationProblem, objectives_df: pd.DataFrame = None):

        self.optimization_problem: OptimizationProblem = optimization_problem
        self._pareto_df: pd.DataFrame = None

        # Maintains a version of the pareto frontier, where all objectives are set to be maximized. So value for the objectives that were
        # originally meant to be minimized, are multiplied by -1.
        #
        self._pareto_df_maximize_all: pd.DataFrame = None

        if objectives_df is not None:
            self.update_pareto(objectives_df)

    @property
    def empty(self) -> bool:
        return (self._pareto_df is None) or self._pareto_df.empty

    @property
    def pareto_df(self) -> pd.DataFrame:
        return self._pareto_df.copy(deep=True)

    def update_pareto(self, objectives_df: pd.DataFrame):
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

        assert all(column in self.optimization_problem.objective_space.dimension_names for column in objectives_df.columns)

        # First, let's turn it into a maximization problem, by flipping the sign of all objectives that are to be minimized.
        #
        pareto_df = self._flip_sign_for_minimized_objectives(objectives_df)

        # By presorting we guarantee, that all dominated points are below the currently considered point.
        #
        pareto_df.sort_values(
            by=[objective.name for objective in self.optimization_problem.objectives],
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

        self._pareto_df_maximize_all = pareto_df

        # Let's unflip the signs
        #
        pareto_df = self._flip_sign_for_minimized_objectives(pareto_df)
        self._pareto_df = pareto_df

    @trace()
    def is_dominated(self, objectives_df) -> pd.Series:
        """For each row in objectives_df checks if the row is dominated by any of the rows in pareto_df.

        :param objectives_df:
        :param pareto_df:
        :return:
        """
        objectives_df = self._flip_sign_for_minimized_objectives(objectives_df)
        is_dominated = pd.Series([False for i in range(len(objectives_df.index))], index=objectives_df.index)
        for idx, pareto_row in self._pareto_df_maximize_all.iterrows():
            is_dominated_by_this_pareto_point = (objectives_df < pareto_row).all(axis=1)
            is_dominated = is_dominated | is_dominated_by_this_pareto_point
        return is_dominated

    def approximate_pareto_volume(self, num_samples=1000000) -> ParetoVolumeEsimator:
        """Approximates the volume of the pareto frontier.

        The idea here is that we can randomly sample from the objective space and observe the proportion of
        dominated points to all points. This proportion will allow us to compute a confidence interval on
        the proportion of dominated points and we can use it to estimate the ratio between the volume of
        the frontier and the volume from which we sampled.

        We can get arbitrarily precise simply by drawing more samples.
        """

        # First we need to find the maxima for each of the objective values.
        #
        objectives_extremes = KeyOrderedDict(ordered_keys=[column for column in self._pareto_df.columns], value_type=float)
        for objective in self.optimization_problem.objectives:
            if objective.minimize:
                objectives_extremes[objective.name] = self._pareto_df[objective.name].min()
            else:
                objectives_extremes[objective.name] = self._pareto_df[objective.name].max()


        random_points_array = np.random.uniform(low=0.0, high=1.0, size=(len(objectives_extremes), num_samples))
        random_objectives_df = pd.DataFrame({
            objective_name: random_points_array[i] * objective_extremum
            for i, (objective_name, objective_extremum)
            in enumerate(objectives_extremes)
        })

        num_dominated_points = self.is_dominated(objectives_df=random_objectives_df).sum()
        return ParetoVolumeEsimator(
            num_random_points=num_samples,
            num_dominated_points=num_dominated_points,
            objectives_maxima=objectives_extremes
        )

    def _flip_sign_for_minimized_objectives(self, df: pd.DataFrame) -> pd.DataFrame:
        """Takes a data frame in objective space and multiplies all minimized objectives by -1.

        The point of this is to convert all problems (minimization and maximization) to maximization problems to simplify
        implementation on everything else.

        :param df:
        :return:
        """
        output_df = df.copy(deep=True)
        for objective in self.optimization_problem.objectives:
            if objective.minimize:
                output_df[objective.name] = -output_df[objective.name]
        return output_df
