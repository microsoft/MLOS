#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances

from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.UtilityFunctionOptimizer import UtilityFunctionOptimizer
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Spaces import CategoricalDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Spaces.HypergridAdapters import DiscreteToUnitContinuousHypergridAdapter
from mlos.Tracer import trace, traced


random_near_incumbent_optimizer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="random_near_incumbent_optimizer_config",
        dimensions=[
            DiscreteDimension(name="num_starting_configs", min=1, max=2**16),
            CategoricalDimension(name="cache_good_params", values=[True, False])
        ]
    ).join(
        on_external_dimension=CategoricalDimension(name="cache_good_params", values=[True]),
        subgrid=SimpleHypergrid(
            name="good_params_cache_config",
            dimensions=[
                DiscreteDimension(name="num_cached_points", min=10, max=2**16),
                DiscreteDimension(name="num_used_points", min=0, max=2**16)
            ]
        )
    ),
    default=Point(
        num_starting_configs=2**10,
        cache_good_params=True,
        good_params_cache_config=Point(
            num_cached_points=2**16,
            num_used_points=2**7
        )
    )
)


class RandomNearIncumbentOptimizer(UtilityFunctionOptimizer):
    """ Searches the utility function for maxima the random near incumbent strategy.

    Starting from an incumbent configuration, this optimizer creates a 'cloud' of random points in the vicinity of the incumbent
    and evaluates the utility function for each of these points. If any of the new points have a higher utility value than the incumbent
    then it gets promoted to the incumbent and we repeat the process.

    Additionally:
        1. The entire process can be batched and the above procedure can happen simultaneously for many "incumbents".
        2. We can intelligently select the starting points by:
            1. Starting with the points on the pareto frontier.
            2. Starting with good points from previous calls to 'suggest' as the utility function evolves gradually.

    The main benefits are:

        1. It doesn't require a gradient, but behaves like a gradient method.
        2. It is well parallelizeable (batchable).

    Possible extensions and options:
        1. We can keep track of the 'velocity' - the assumption being that if we are moving in a given direction, we can try
            accelerating in that direction until it's no longer profitable. Check out ADAM and similar gradient based methods
            for inspiration.
        2. We should have several distributions to work with.


    """

    def __init__(
            self,
            optimizer_config: Point,
            optimization_problem: OptimizationProblem,
            utility_function: UtilityFunction,
            pareto_frontier: ParetoFrontier,
            logger=None
    ):
        UtilityFunctionOptimizer.__init__(self, optimizer_config, optimization_problem, utility_function, logger)

        self.parameter_adapter = DiscreteToUnitContinuousHypergridAdapter(
            adaptee=self.optimization_problem.parameter_space
        )
        self.dimension_names = [dimension.name for dimension in self.parameter_adapter.dimensions]
        self.pareto_frontier = pareto_frontier

        # We will cache good configs from past invocations here.
        #
        self._good_configs_from_the_past_invocations_df = None

    @trace()
    def suggest(self, context_values_dataframe: pd.DataFrame = None):
        """ Returns the next best configuration to try.

        The idea is pretty simple:
            1. We start with all configs on the pareto frontier, plus some good points from previous calls to suggest plus some random configs.
            2. For each point we generate random neighbors and optionally adjust them using our velocity.
            3. We compute utility for all neighbors and select a new incumbent.
            4. We update the velocity.
            5. We repeat until we ran out of iterations or until velocity falls below some threshold.

        """

        initial_params_df = self._prepare_initial_params_df()



        feature_values_dataframe = self.optimization_problem.parameter_space.random_dataframe(
            num_samples=self.optimizer_config.num_worms * self.optimizer_config.num_initial_points_multiplier
        )
        utility_function_values = self.utility_function(feature_values_pandas_frame=feature_values_dataframe.copy(deep=False))
        num_utility_function_values = len(utility_function_values.index)
        if num_utility_function_values == 0:
            config_to_suggest = Point.from_dataframe(feature_values_dataframe.iloc[[0]])
            self.logger.debug(f"Suggesting: {str(config_to_suggest)} at random.")
            return config_to_suggest

        # TODO: keep getting configs until we have enough utility values to get started. Or assign 0 to missing ones,
        #  and let them climb out of their infeasible holes.
        top_utility_values = utility_function_values.nlargest(n=self.optimizer_config.num_worms, columns=['utility'])

        # TODO: could it be in place?
        features_for_top_utility = self.parameter_adapter.project_dataframe(feature_values_dataframe.loc[top_utility_values.index], in_place=False)
        worms = pd.concat([features_for_top_utility, top_utility_values], axis=1)
        # Let's reset the index to make keeping track down the road easier.
        #
        worms.index = pd.Index(range(len(worms.index)))

        # Initialize luciferin to the value of the utility function
        #
        worms['decision_radius'] = self.optimizer_config.initial_decision_radius
        worms['luciferin'] = worms['utility']

        for _ in range(self.optimizer_config.num_iterations):
            worms = self.run_iteration(worms=worms)
            # TODO: keep track of the max configs over iterations
            worms = self.compute_utility(worms)
            worms['luciferin'] = (1 - self.optimizer_config.luciferin_decay_constant) * worms['luciferin'] + \
                                 self.optimizer_config.luciferin_enhancement_constant * worms['utility']

        # TODO: return the max of all seen configs - not just the configs that the glowworms occupied in this iteration.
        idx_of_max = worms['utility'].idxmax()
        best_config = worms.loc[[idx_of_max], self.dimension_names]
        config_to_suggest = Point.from_dataframe(best_config)
        self.logger.debug(f"Suggesting: {str(config_to_suggest)} at random.")
        # TODO: we might have to go for second or nth best if the projection won't work out. But then again if we were
        # TODO: able to compute the utility function then the projection has worked out once before...
        return self.parameter_adapter.unproject_point(config_to_suggest)

    @trace()
    def _prepare_initial_params_df(self):
        """Prepares a dataframe with inital parameters to start the search with.

        We simply take all points on the pareto frontier, if there is not enough points there, we also grab some good points from
        the past, if there still isn't enough, then we generate random points.
        :return:
        """
        initial_params_df = self.pareto_frontier.params_for_pareto_df

        if self._good_configs_from_the_past_invocations_df is not None and len(self._good_configs_from_the_past_invocations_df.index) > 0:
            if len(initial_params_df.index) < self.optimizer_config.num_starting_configs and self.optimizer_config.cache_good_params:
                # We add some samples from the cached ones.
                num_cached_points_to_use = min(
                    len(self._good_configs_from_the_past_invocations_df.index),
                    self.optimizer_config.good_params_cache_config.num_used_points
                )

                cached_points_to_use_df = self._good_configs_from_the_past_invocations_df.sample(
                    num=num_cached_points_to_use,
                    replace=False,
                    axis='index'
                )
                initial_params_df = pd.concat([initial_params_df, cached_points_to_use_df])

        if len(initial_params_df.index) < self.optimizer_config.num_starting_configs:
            # If we are still short some points, we generate them at random.
            num_random_points_to_create = self.optimizer_config.num_starting_configs - len(initial_params_df.index)
            random_params_df = self.optimization_problem.parameter_space.random_dataframe(num_samples=num_random_points_to_create)
            initial_params_df = pd.concat([initial_params_df, random_params_df])

        initial_params_df.reset_index(drop=True, inplace=True)
        return initial_params_df


    @trace()
    def compute_utility(self, worms):
        """ Computes utility function values for each worm.

        Since some worm positions will produce a NaN, we need to keep producing new utility values for those.

        :param worms:
        :return:
        """
        unprojected_features = self.parameter_adapter.unproject_dataframe(worms[self.dimension_names], in_place=False)
        utility_function_values = self.utility_function(unprojected_features.copy(deep=False))
        worms['utility'] = utility_function_values
        index_of_nans = worms.index.difference(utility_function_values.index)
        # TODO: A better solution would be to give them random valid configs, and let them live.
        # TODO: BUT avoid calling the utility function again for just a few samples - just let them hang on for an iteration.
        worms.drop(index=index_of_nans, inplace=True)
        worms.reset_index(drop=True, inplace=True)
        return worms

    @trace()
    def run_iteration(self, worms: pd.DataFrame):

        with traced(scope_name="numpy_matrix_operations"):
            positions = worms[self.dimension_names].to_numpy()
            # At this point many glowworms will have NaNs in their position vectors: for every column that's invalid.
            # Glowworms with the same set of valid columns, belong to the same subgrids in the hypergrid, but glowworms
            # with different set of valid columns belong to - essentially - different search spaces, and the idea of
            # distance ceases to make sense. But their positions are all cast onto this really high dimensional space.
            # How can we keep them apart?
            #
            # Here is the trick: glowworms should only see other glowworms in their own search space. One way to
            # accomplish that is to fill in the NaNs with a value larger than the max_sensory_radius. Now, glowworms
            # in different subgrids will never see each other (they can't see that far in this space), but glowworms in
            # the same subgrids will have the same large placeholder in their invalid dimensions, so it will not contribute
            # anything to the distance between them.
            positions = np.nan_to_num(x=positions, copy=False, nan=2*self.optimizer_config.max_sensory_radius)

            distances = euclidean_distances(positions, positions)
            decision_radii = worms['decision_radius'].to_numpy().transpose()

            # Subtract the sensory radius from each row. Everything in the row, that's negative is your neighbor (if they
            # also have a higher luciferin level).
            #
            distances = (distances - decision_radii).transpose()

            # Now let's compute the difference in luciferin. Numpy's broadcasting is hard to read, but fast and convenient.
            # We are basically doing exactly the same thing with luciferin as with distances: whatever is left negative in
            # your row is your neighbor (if they are also close enough).
            #
            luciferin = worms['luciferin'].to_numpy()
            luciferin_diffs = luciferin[:, np.newaxis] - luciferin

            # So worms are neighbors if both signs are negative.
            #
            distances_signs = np.sign(distances)
            luciferin_signs = np.sign(luciferin_diffs)
            summed_signs = distances_signs + luciferin_signs

            # Now let's put together a matrix, such that in each row for each column we have either:
            #  0 - if the worm in that column is not a neighbor (too far or too dim)
            #  or luciferin difference between that neighbor and us.
            #
            unnormalized_probability = np.where(summed_signs == -2, -luciferin_diffs, 0)

        # We will have to iterate over all rows anyway, to invoke the np.random.choice() since it operates on
        # 1-D arrays so we might as well iterate over unnormalized probabilities, check if there is anything
        # non-zero in there, select the target, compute, and take the step.
        #
        for row, unnormalized_probability_row in enumerate(unnormalized_probability):
            row_sum = unnormalized_probability_row.sum()
            num_neighbors = np.count_nonzero(unnormalized_probability_row)
            if row_sum == 0:
                # nobody is close enough and bright enough
                continue
            normalized_probability = unnormalized_probability_row / row_sum
            col = np.random.choice(len(normalized_probability), size=1, p=normalized_probability)[0]
            our_position = positions[row]
            their_position = positions[col]
            distance = distances[row][col]
            step_unit_vector = (their_position - our_position) / distance
            step = self.optimizer_config.step_size * step_unit_vector
            our_new_position = our_position + step

            # We only set the non-nan values in the worms dataframe. Remember the trick of setting nans to big values?
            # This is undoing that trick to hide it from the caller.
            # TODO: this ends up being pretty slow. See if we can improve.
            #
            is_nan = np.isnan(worms.loc[row, self.dimension_names].to_numpy())
            our_new_position[is_nan] = np.nan
            worms.loc[row, self.dimension_names] = our_new_position

            current_decision_radius = decision_radii[row]
            decision_radius_update = self.optimizer_config.decision_radius_adjustment_constant * \
                                     (self.optimizer_config.desired_num_neighbors - num_neighbors)

            new_decision_radius = min(
                self.optimizer_config.max_sensory_radius,
                max(0, current_decision_radius + decision_radius_update)
            )
            worms.loc[row, ['decision_radius']] = new_decision_radius
        return worms
