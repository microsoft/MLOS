#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np
import pandas as pd

from mlos.Exceptions import UnableToProduceGuidedSuggestionException, UtilityValueUnavailableException
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.UtilityFunctionOptimizer import UtilityFunctionOptimizer
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Spaces import ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Spaces.HypergridAdapters import DiscreteToUnitContinuousHypergridAdapter
from mlos.Tracer import trace, traced


random_near_incumbent_optimizer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="random_near_incumbent_optimizer_config",
        dimensions=[
            DiscreteDimension(name="num_starting_configs", min=1, max=1000),
            ContinuousDimension(name="initial_velocity", min=0.01, max=1),
            ContinuousDimension(name="velocity_update_constant", min=0, max=1),
            ContinuousDimension(name="velocity_convergence_threshold", min=0, max=1),
            DiscreteDimension(name="max_num_iterations", min=1, max=1000),
            DiscreteDimension(name="num_neighbors", min=1, max=1000),
            DiscreteDimension(name="num_cached_good_params", min=0, max=2**16),
            ContinuousDimension(name="initial_points_pareto_weight", min=0, max=1),
            ContinuousDimension(name="initial_points_cached_good_params_weight", min=0, max=1),
            ContinuousDimension(name="initial_points_random_params_weight", min=0, max=1),
        ]
    ),
    default=Point(
        num_starting_configs=10,
        initial_velocity=0.3,
        velocity_update_constant=0.5,
        velocity_convergence_threshold=0.01,
        max_num_iterations=50,
        num_neighbors=20,
        num_cached_good_params=2**10,
        initial_points_pareto_weight=0.5,
        initial_points_cached_good_params_weight=0.3,
        initial_points_random_params_weight=0.2
    ),
    description="""
    * num_starting_configs - how many points to start the search from?
    * initial_velocity - how far from the incumbent should the random neighbors be generated?
    * velocity_update_constant - how quickly to change the velocity (0 - don't change it at all, 1 - change it as fast as possible)?
    * velocity_convergence_threshold - when an incumbent's velocity drops below this threshold, it is assumed to have converged.
    * max_num_iterations - cap on the number of iterations. A failsafe - should be higher than what the algorithm needs to converge on average.
    * num_neighbors - how many random neighbors to generate for each incumbent?
    * num_cached_good_params - how many good configurations should this optimizer cache for future use?
    * initial_points_pareto_weight - what proportion of initial points should come from the pareto frontier?
    * initial_points_cached_good_params_weight - what proportion of initial points should come from the good params cache?
    * initial_points_random_params_weight - what proportion of initial points should be randomly generated?
    """
)

random_near_incumbent_optimizer_config_store.add_config_by_name(
    config_name="20_incumbents_50_neighbors",
    config_point=Point(
        num_starting_configs=20,
        initial_velocity=0.2,
        velocity_update_constant=0.3,
        velocity_convergence_threshold=0.01,
        max_num_iterations=15,
        num_neighbors=50,
        num_cached_good_params=2**10,
        initial_points_pareto_weight=0.5,
        initial_points_cached_good_params_weight=0.3,
        initial_points_random_params_weight=0.2
    ),
    description="More thorough and more expensive than the default."
)

class RandomNearIncumbentOptimizer(UtilityFunctionOptimizer):
    """ Searches the utility function for maxima using the random near incumbent strategy.

        Starting from an incumbent configuration, this optimizer creates a 'cloud' of random points in the incumbent's vicinity
    and evaluates the utility function for each of these points. If any of the new points has a higher utility value than the
    incumbent then it gets promoted to the incumbent and we repeat the process.

    **Velocity**

        We keep track the size of the step that each incumbent takes in each iteration. We then adjust that incumbent's velocity
    (i.e. the radius within which it generates random neighbors). If the new incumbent is really far from the current incumbent
    we assume that we should move faster in that direction and we increase velocity accordingly. Conversely, if the displacement
    between the old and new incumbent is small, we reduce the velocity to allow the optimizer to more thoroughly exploit what
    appears to be a local maximum. If the displacement continues to be small, we continue to reduce the velocity, until eventually
    it falls below the velocity_convergence_threshold. That's when we assume the optimizer has converged for that incumbent.

    **Parallelism**

        The above algorithm is trivial to parallelize. We instantiate num_starting_configs incumbents as a mix of pareto points,
    known good configs from previous iterations, and brand new random configs. On each iteration, we generate random neighbors
    for each incumbent, then update their positions and velocities independently. Importantly, once a given incumbent converges,
    it donates its neighbors budget to all remaining active incumbents. This is because the total number of iterations this
    algorithm needs to converge equals the number of iterations the slowest incumbent needs. So we want all incumbents that finish
    quickly, to help the laggards so that the whole process can finish in as few iterations as possible.

    **Starting Points**

        Utility function optimizers are invoked repeatedly to find maxima of utility functions that change only slightly between
    subsequent iterations. So we should be able to utilize learnings from prior iterations to speed up search for utility function
    maxima in subsequent calls. We do this by:
        * using points on the pareto frontier as some of the starting points,
        * using good points from past iterations as some of the starting points.

        Additionally, we use some random points as starting points too to balance the explore-exploit tradeoff.



    **Benefits**

    The main benefits of this implementation are:

        1. It doesn't require a gradient, but behaves similarly to a gradient method.
        2. It can be easily parallelized.
        3. We exploit prior experience by intelligently selecting starting points, thus making more efficient use of our compute resources.

    **Extensions**

        Some of the possible extensions include:
         * implementing different distributions from which to draw neighbors.
         * adding other momentum-like methods to change the incumbents' velocity.


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
        self.parameter_dimension_names = [dimension.name for dimension in self.parameter_adapter.dimensions]
        self.pareto_frontier = pareto_frontier

        # We will cache good configs from past invocations here.
        #
        self._good_configs_from_the_past_invocations_df = None

    @trace()
    def suggest(self, context_values_dataframe: pd.DataFrame = None):
        """ Returns the next best configuration to try.

        The idea is pretty simple:
            1. We start with some configs on the pareto frontier, plus some good points from previous calls to suggest plus some random configs.
            2. For each point we generate random neighbors and optionally adjust them using our velocity.
            3. We compute utility for all neighbors and select a new incumbent.
            4. We update the velocity.
            5. We repeat until we run out of iterations or until velocity falls below some threshold.

        """
        self.logger.info(f"Suggesting config for context: {context_values_dataframe}")

        assert context_values_dataframe is None or len(context_values_dataframe.index) == 1

        incumbent_params_df = self._prepare_initial_params_df()
        incumbent_utility_df = self._compute_utility_for_params(params_df=incumbent_params_df, context_df=context_values_dataframe)

        if len(incumbent_utility_df.index) == 0:
            error_message = f"Utility function {self.utility_function.__class__.__name__} produced no values."
            self.logger.info(error_message)
            raise UtilityValueUnavailableException(error_message)

        # Before we can create random neighbors, we need to normalize all parameter values by projecting them into unit hypercube.
        #
        projected_incumbent_params_df = self.parameter_adapter.project_dataframe(df=incumbent_params_df, in_place=False)

        # Now, let's put together our incumbents_df which contains the projected params, the accompanying utiliy, as well as the velocity
        # component along each dimension.
        incumbents_df = projected_incumbent_params_df
        incumbents_df['utility'] = incumbent_utility_df['utility']

        incumbents_df['speed'] = 0
        for dimension_name in self.parameter_dimension_names:
            incumbents_df[f'{dimension_name}_velocity'] = self.optimizer_config.initial_velocity
            incumbents_df['speed'] += self.optimizer_config.initial_velocity ** 2

        incumbents_df['speed'] = np.sqrt(incumbents_df['speed'])
        incumbents_df['active'] = incumbents_df['speed'] > self.optimizer_config.velocity_convergence_threshold

        # Let's disable all incumbents for which we couldn't compute utility.
        #
        null_utility_index = incumbents_df[incumbents_df['utility'].isna()].index
        incumbents_df.loc[null_utility_index, 'active'] = False

        num_iterations = 0

        while num_iterations < self.optimizer_config.max_num_iterations and incumbents_df['active'].any():
            num_iterations += 1
            incumbents_df = self._run_iteration(incumbents_df, context_df=context_values_dataframe, iteration_number=num_iterations)

        if incumbents_df['utility'].isna().all():
            error_message = "Utility values were not available for the incumbent."
            self.logger.info(error_message)
            raise UtilityValueUnavailableException(error_message)

        if num_iterations == 0:
            error_message = f"{self.__class__.__name__} performed 0 iterations."
            self.logger.info(error_message)
            raise UnableToProduceGuidedSuggestionException(error_message)

        if incumbents_df.dtypes['utility'] != np.float:
            self.logger.info(
                f"The type of incumbents_df['utility'] is {incumbents_df.dtypes['utility']}. Utility function: {self.utility_function.__class__.__name__}, "
                f"incumbents_df length: {len(incumbents_df.index)}"
            )
            incumbents_df['utility'] = pd.to_numeric(arg=incumbents_df['utility'], errors='raise')

        self._cache_good_incumbents(incumbents_df)

        idx_of_max = incumbents_df['utility'].idxmax()
        best_config_df = incumbents_df.loc[[idx_of_max], self.parameter_dimension_names]
        config_to_suggest = Point.from_dataframe(best_config_df)
        unprojected_config_to_suggest = self.parameter_adapter.unproject_point(config_to_suggest)
        self.logger.info(f"After {num_iterations} iterations suggesting: {unprojected_config_to_suggest.to_json(indent=2)}")
        return unprojected_config_to_suggest


    @trace()
    def _run_iteration(self, incumbents_df: pd.DataFrame, context_df: pd.DataFrame, iteration_number: int) -> pd.DataFrame:
        # Let's create random neighbors for each of the initial params
        #
        all_neighbors_df, unprojected_neighbors_df = self._prepare_random_neighbors(incumbents_df=incumbents_df)

        neighbors_utility_df = self._compute_utility_for_params(params_df=unprojected_neighbors_df, context_df=context_df)
        self.logger.info(f"Computed utility for {len(neighbors_utility_df.index)} random neighbors.")

        all_neighbors_df = all_neighbors_df.loc[neighbors_utility_df.index]
        all_neighbors_df['utility'] = neighbors_utility_df['utility']
        all_neighbors_df['utility_gain'] = all_neighbors_df['utility'] - all_neighbors_df['incumbent_utility']

        # We can filter out all rows with negative utility gain.
        #
        all_neighbors_df = all_neighbors_df[all_neighbors_df['utility_gain'] >= 0]
        self.logger.info(f"{len(all_neighbors_df.index)} have positive utility gain.")

        # The series below has best neighbor's index as value and the incumbent_config_idx as index.
        #
        best_neighbors_indices = all_neighbors_df.groupby(by=["incumbent_config_idx"])['utility_gain'].idxmax()
        best_neighbors_df = all_neighbors_df.loc[best_neighbors_indices]
        best_neighbors_df.set_index(keys=best_neighbors_indices.index, inplace=True, verify_integrity=True)
        self.logger.info(f"{len(best_neighbors_df.index)} neighbors improved upon their respective incumbents.")

        # Let's create a dataframe with the new incumbents. We do it by first copying old incumbents in case none of their neighbors had higher utility.
        # Subsequently we copy over any neighbors, that had a positive utility gain.
        #
        new_incumbents_df = incumbents_df[self.parameter_dimension_names].copy()
        new_incumbents_df['utility'] = incumbents_df['utility']
        new_incumbents_df.loc[best_neighbors_df.index, self.parameter_dimension_names] = best_neighbors_df[self.parameter_dimension_names]
        new_incumbents_df.loc[best_neighbors_df.index, 'utility'] = best_neighbors_df['utility']

        # We need to compute the displacement for this iteration. We will use it to alter the speed.
        #
        displacement_df = pd.DataFrame()
        for dimension_name in self.parameter_dimension_names:
            displacement_df[dimension_name] = new_incumbents_df[dimension_name] - incumbents_df[dimension_name]
        displacement_df.fillna(0, inplace=True)

        # Finally we get to update the parameter values for incumbents, as well as updating their velocity.
        #
        incumbents_df['speed'] = 0
        for dimension_name in self.parameter_dimension_names:
            incumbents_df[dimension_name] = new_incumbents_df[dimension_name]
            incumbents_df[f'{dimension_name}_velocity'] = \
                incumbents_df[f'{dimension_name}_velocity'] * (1 - self.optimizer_config.velocity_update_constant) \
                + displacement_df[dimension_name] * self.optimizer_config.velocity_update_constant

            incumbents_df['speed'] += incumbents_df[f'{dimension_name}_velocity'] ** 2

        incumbents_df['speed'] = np.sqrt(incumbents_df['speed'])
        incumbents_df['active'] = incumbents_df['active'] & (incumbents_df['speed'] > self.optimizer_config.velocity_convergence_threshold)

        # Let's set the velocity of all inactive incumbents to 0.
        #
        inactive_incumbents_index = incumbents_df[~incumbents_df['active']].index
        for dimension_name in self.parameter_dimension_names:
            incumbents_df.loc[inactive_incumbents_index, f'{dimension_name}_velocity'] = 0
        incumbents_df.loc[inactive_incumbents_index, 'speed'] = 0

        # We also get to update their utility.
        #
        not_na_incumbent_index = incumbents_df[incumbents_df['utility'].notna()].index
        assert (incumbents_df.loc[not_na_incumbent_index, 'utility'] <= new_incumbents_df.loc[not_na_incumbent_index, 'utility']).all()
        incumbents_df['utility'] = new_incumbents_df['utility']

        return incumbents_df

    @trace()
    def _prepare_initial_params_df(self):
        """Prepares a dataframe with initial parameters to start the search with.

            First, we look at how many points from the pareto frontier we want. We grab this many at random from the pareto_df, unless
        the pareto has fewer points than that in which case we simply take all of them.

            Secondly, we look at how many good points from previous iterations we want. We take as many at random from the cache, unless
        the cache doesn't have that many in which case we take all cached points.

            Lastly, generate the rest of the points at random.

        :return:
        """
        self.logger.info("Preparing initial params")

        # First we must normalize the weights.
        #
        total_weights = self.optimizer_config.initial_points_pareto_weight \
                        + self.optimizer_config.initial_points_cached_good_params_weight \
                        + self.optimizer_config.initial_points_random_params_weight
        assert total_weights > 0

        initial_points_pareto_fraction = self.optimizer_config.initial_points_pareto_weight / total_weights
        initial_points_cached_good_fraction = self.optimizer_config.initial_points_cached_good_params_weight / total_weights

        num_initial_points = self.optimizer_config.num_starting_configs

        # Let's start with the pareto points.
        #
        pareto_params_df = self.pareto_frontier.params_for_pareto_df
        if pareto_params_df is None:
            pareto_params_df = pd.DataFrame()

        num_desired_pareto_points = math.floor(num_initial_points * initial_points_pareto_fraction)
        num_existing_pareto_points = len(pareto_params_df.index)

        if num_existing_pareto_points > 0:
            if num_desired_pareto_points < num_existing_pareto_points:
                pareto_params_df = pareto_params_df.sample(n=num_desired_pareto_points, replace=False, axis='index')
            self.logger.info(f"Using {len(pareto_params_df.index)} of {num_existing_pareto_points} pareto points as starting configs.")
        else:
            self.logger.info("There are no existing pareto points.")

        # Now let's take the cached good points.
        #
        num_desired_cached_good_points = math.floor(num_initial_points * initial_points_cached_good_fraction)
        cached_params_df = pd.DataFrame()
        if self._good_configs_from_the_past_invocations_df is not None:
            if num_desired_cached_good_points < len(self._good_configs_from_the_past_invocations_df.index):
                cached_params_df = self._good_configs_from_the_past_invocations_df.sample(n=num_desired_cached_good_points, replace=False, axis='index')
            else:
                cached_params_df = self._good_configs_from_the_past_invocations_df.copy(deep=True)
            self.logger.info(
                f"Using {len(cached_params_df.index)} out of {len(self._good_configs_from_the_past_invocations_df.index)} "
                f"cached good configs as starting configs"
            )
        else:
            self.logger.info("No cached params are available.")

        # Finally, let's generate the random points.
        #
        num_desired_random_points = num_initial_points - len(pareto_params_df.index) - len(cached_params_df.index)
        random_params_df = self.optimization_problem.parameter_space.random_dataframe(num_samples=num_desired_random_points)
        self.logger.info(f"Using {len(random_params_df.index)} random points as starting configs.")

        initial_params_df = pd.concat([pareto_params_df, cached_params_df, random_params_df])
        initial_params_df.reset_index(drop=True, inplace=True)
        return initial_params_df


    @trace()
    def _cache_good_incumbents(self, incumbents_df: pd.DataFrame):
        """Caches good incumbent values to use in subsequent iterations."""

        if self.optimizer_config.num_cached_good_params == 0:
            return

        incumbents_df = incumbents_df[self.parameter_dimension_names]
        unprojected_incumbents_df = self.parameter_adapter.unproject_dataframe(incumbents_df, in_place=False)

        if self._good_configs_from_the_past_invocations_df is None:
            self._good_configs_from_the_past_invocations_df = unprojected_incumbents_df
        else:
            self._good_configs_from_the_past_invocations_df = pd.concat([self._good_configs_from_the_past_invocations_df, unprojected_incumbents_df])

        if len(self._good_configs_from_the_past_invocations_df.index) > self.optimizer_config.num_cached_good_params:
            self._good_configs_from_the_past_invocations_df = self._good_configs_from_the_past_invocations_df.sample(
                n=self.optimizer_config.num_cached_good_params,
                replace=False
            )

    @trace()
    def _compute_utility_for_params(self, params_df: pd.DataFrame, context_df: pd.DataFrame):
        """This functionality is repeated a couple times so let's make sure it is in one place.

        Basically we only need to create a features_df from params_df and context_df, and invoke the utility function.
        """
        features_df = self.optimization_problem.construct_feature_dataframe(
            parameters_df=params_df,
            context_df=context_df,
            product=True
        )
        utility_df = self.utility_function(feature_values_pandas_frame=features_df)
        assert utility_df.dtypes['utility'] == np.float,\
            f"{utility_df} produced by {self.utility_function.__class__.__name__} has the wrong type for the 'utility' column: {utility_df.dtypes['utility']}"
        return utility_df

    @trace()
    def _prepare_random_neighbors(self, incumbents_df: pd.DataFrame):
        active_incumbents_df = incumbents_df[incumbents_df['active']]
        num_active_incumbents = len(active_incumbents_df.index)

        # Since we have fewer active incumbents, each can have a few more neighbors, which should speed up convergence.
        #
        num_neighbors_per_incumbent = math.floor(
            self.optimizer_config.num_neighbors * len(incumbents_df.index) / num_active_incumbents)
        self.logger.info(
            f"Num active incumbents: {num_active_incumbents}/{len(incumbents_df.index)}, num neighbors per incumbent: {num_neighbors_per_incumbent}"
        )

        neighbors_dfs = []

        for incumbent_config_idx, incumbent in active_incumbents_df.iterrows():
            # For now let's only do normal distribution but we can add options later.
            #
            neighbors_df = pd.DataFrame()
            for dimension_name in self.parameter_dimension_names:
                neighbors_df[dimension_name] = np.random.normal(
                    loc=incumbent[dimension_name],
                    scale=np.abs(incumbent[f'{dimension_name}_velocity']),
                    size=num_neighbors_per_incumbent
                )

            # Let's remember which config generated these neighbors too
            #
            neighbors_df['incumbent_config_idx'] = incumbent_config_idx

            # It's much simpler to remember the incumbent utility now, then to try to find it later.
            #
            neighbors_df['incumbent_utility'] = incumbent['utility']
            neighbors_dfs.append(neighbors_df)

        all_neighbors_df = pd.concat(neighbors_dfs, ignore_index=True)

        # Let's remove all obviously invalid configs. This call uses fast vectorized operations, but since filtering happens on a flattened
        # grid, it doesn't check the ancestral dependencies. Thus, it will only filter out the points which fall outside the min-max range.
        #
        num_neighbors_including_invalid = len(all_neighbors_df.index)
        all_neighbors_df_no_nulls = all_neighbors_df.fillna(0, inplace=False)
        probably_valid_neighbors_index = self.parameter_adapter.get_valid_rows_index(original_dataframe=all_neighbors_df_no_nulls)
        all_neighbors_df = all_neighbors_df.loc[probably_valid_neighbors_index]
        num_neighbors_after_filtering_out_projected_points = len(probably_valid_neighbors_index)

        # The all_neighbors_df contains parameters in the unit-continuous hypergrid. So we need to unproject it back to the original
        # hierarchical hypergrid with many parameter types.
        #
        unprojected_neighbors_df = self.parameter_adapter.unproject_dataframe(df=all_neighbors_df, in_place=False)

        # Now that we have the hierarchy back, we can once again filter out invalid rows, this time making sure that all ancestral dependencies
        # are honored. For hierarchical spaces, filter_out_invalid_rows() function is not vectorized (yet) so it's slow. Thus it pays, to first
        # remove all obviously wrong rows above, and only examine the smaller subset here. TODO: vectorize filter_out_invalid_rows() for hierachical
        # spaces.
        #
        unprojected_neighbors_df = self.optimization_problem.parameter_space.filter_out_invalid_rows(
            original_dataframe=unprojected_neighbors_df,
            exclude_extra_columns=False
        )

        num_neighbors_after_filtering_out_unprojected_points = len(unprojected_neighbors_df.index)
        self.logger.info(
            f"Started with {num_neighbors_including_invalid}. "
            f"Adapter filtered them down to {num_neighbors_after_filtering_out_projected_points}. "
            f"Parameter space filtered them down to {num_neighbors_after_filtering_out_unprojected_points}"
        )

        return all_neighbors_df, unprojected_neighbors_df
