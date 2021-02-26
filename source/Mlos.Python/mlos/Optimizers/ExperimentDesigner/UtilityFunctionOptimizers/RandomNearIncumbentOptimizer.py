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
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Spaces.HypergridAdapters import DiscreteToUnitContinuousHypergridAdapter
from mlos.Tracer import trace, traced


random_near_incumbent_optimizer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="random_near_incumbent_optimizer_config",
        dimensions=[
            DiscreteDimension(name="num_starting_configs", min=1, max=2**16),
            ContinuousDimension(name="initial_velocity", min=0.01, max=1),
            ContinuousDimension(name="velocity_update_constant", min=0, max=1),
            ContinuousDimension(name="velocity_convergence_threshold", min=0, max=1),
            ContinuousDimension(name="max_num_iterations", min=1, max=1000),
            DiscreteDimension(name="num_neighbors", min=1, max=1000),
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
        num_starting_configs=100,
        initial_velocity=0.05,
        velocity_update_constant=0.1,
        velocity_convergence_threshold=0.01,
        max_num_iterations=10,
        num_neighbors=100,
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
        self.parameter_dimension_names = [dimension.name for dimension in self.parameter_adapter.dimensions]
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

        assert context_values_dataframe is None or len(context_values_dataframe.index) == 1

        incumbent_params_df = self._prepare_initial_params_df()

        # Now that we have the initial incumbent parameters, we need to compute their utility.
        #
        incumbent_features_df = self.optimization_problem.construct_feature_dataframe(
            parameter_values=incumbent_params_df,
            context_values=context_values_dataframe,
            product=False
        )
        incumbent_utility_df = self.utility_function(feature_values_pandas_frame=incumbent_features_df)

        # Before we can create random neighbors, we need to normalize all parameter values by projecting them into unit hypercube.
        #
        projected_incumbent_params_df = self.parameter_adapter.project_dataframe(df=incumbent_params_df, in_place=False)

        # Now, let's put together our incumbents_df which contains the projected params, the accompanying utiliy, as well as the velocity
        # component along each dimension.
        incumbents_df = projected_incumbent_params_df
        incumbents_df['utility'] = incumbent_utility_df['utility']
        for dimension_name in self.parameter_dimension_names:
            incumbents_df[f'{dimension_name}_velocity'] = self.optimizer_config.initial_velocity

        num_iterations = 0

        # Just for development we can keep track of utility values and velocities over time.
        #
        utility_over_time = []
        velocities_over_time = {
            dimension_name: []
            for dimension_name
            in self.parameter_dimension_names
        }


        while num_iterations < self.optimizer_config.max_num_iterations:
            utility_over_time.append(incumbents_df['utility'].copy())
            for dimension_name in self.parameter_dimension_names:
                velocities_over_time[dimension_name].append(incumbents_df[f'{dimension_name}_velocity'].copy())

            num_iterations += 1

            # Let's create random neighbors for each of the initial params
            #
            neighbors_dfs = []
            for incumbent_config_idx, incumbent in incumbents_df.iterrows():
                # For now let's only do normal distribution but we can add options later.
                #
                neighbors_df = pd.DataFrame()
                for dimension_name in self.parameter_dimension_names:
                    neighbors_df[dimension_name] = np.random.normal(
                        loc=incumbent[dimension_name],
                        scale=np.abs(incumbent[f'{dimension_name}_velocity']),
                        size=self.optimizer_config.num_neighbors
                    )

                # Let's remove all invalid configs. TODO: consider clipping them instead.
                #
                neighbors_df = self.parameter_adapter.filter_out_invalid_rows(original_dataframe=neighbors_df, exclude_extra_columns=False)

                # Let's remember which config generated these neighbors too
                #
                neighbors_df['incumbent_config_idx'] = incumbent_config_idx
                neighbors_df['incumbent_utility'] = incumbent['utility']
                neighbors_dfs.append(neighbors_df)

            all_neighbors_df = pd.concat(neighbors_dfs, ignore_index=True)

            # Next, we compute utility for all of those random neighbors
            #
            unprojected_neighbors_df = self.parameter_adapter.unproject_dataframe(df=all_neighbors_df, in_place=False)

            assert len(unprojected_neighbors_df.index) == len(self.optimization_problem.parameter_space.get_valid_rows_index(unprojected_neighbors_df))


            neighbors_features_df = self.optimization_problem.construct_feature_dataframe(
                parameter_values=unprojected_neighbors_df,
                context_values=context_values_dataframe,
                product=False
            )

            neighbors_utility_df = self.utility_function(feature_values_pandas_frame=neighbors_features_df)
            all_neighbors_df = all_neighbors_df.loc[neighbors_utility_df.index]
            all_neighbors_df['utility'] = neighbors_utility_df['utility']
            all_neighbors_df['utility_gain'] = all_neighbors_df['utility'] - all_neighbors_df['incumbent_utility']

            # We can filter out all rows with negative utility gain.
            #
            all_neighbors_df = all_neighbors_df[all_neighbors_df['utility_gain'] > 0]

            # The series below has best neighbor's index as value and the incumbent_config_idx as key.
            #
            best_neighbors_indices = all_neighbors_df.groupby(by=["incumbent_config_idx"])['utility_gain'].idxmax()
            best_neighbors_df = all_neighbors_df.loc[best_neighbors_indices]
            best_neighbors_df.set_index(keys=best_neighbors_indices.index, inplace=True, verify_integrity=True)

            # Let's create a dataframe with the new incumbents. We do it by copying old incumbents in case none of their neighbors
            # had higher utility.
            new_incumbents_df = incumbents_df[self.parameter_dimension_names].copy()
            new_incumbents_df['utility'] = incumbents_df['utility']
            new_incumbents_df.loc[best_neighbors_df.index, self.parameter_dimension_names] = best_neighbors_df[self.parameter_dimension_names]
            new_incumbents_df.loc[best_neighbors_df.index, 'utility'] = best_neighbors_df['utility']

            # We need to compute the displacement for this iteration.
            #
            displacement_df = pd.DataFrame()
            for dimension_name in self.parameter_dimension_names:
                displacement_df[dimension_name] = new_incumbents_df[dimension_name] - incumbents_df[dimension_name]

            # Finally we get to update the parameter values for incumbents, as well as updating their velocity.
            #
            for dimension_name in self.parameter_dimension_names:
                incumbents_df[dimension_name] = new_incumbents_df[dimension_name]
                incumbents_df[f'{dimension_name}_velocity'] = incumbents_df[f'{dimension_name}_velocity'] * (1 - self.optimizer_config.velocity_update_constant) \
                                                              + displacement_df[dimension_name] * self.optimizer_config.velocity_update_constant
            # We also get to update their utility.
            #
            if not (incumbents_df['utility'] <= new_incumbents_df['utility']).all():
                print("breakpoint")
            incumbents_df['utility'] = new_incumbents_df['utility']



        utility_over_time.append(incumbents_df['utility'])
        for dimension_name in self.parameter_dimension_names:
            velocities_over_time[dimension_name].append(incumbents_df[f'{dimension_name}_velocity'])

        utilitity_over_time_df = pd.concat(utility_over_time, axis=1).T
        velocity_over_time_dfs = {}
        for dimension_name in self.parameter_dimension_names:
            velocity_over_time_dfs[dimension_name] = pd.concat(velocities_over_time[dimension_name], axis=1).T

        print('breakpoint')


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
