#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances

from mlos.Exceptions import UtilityValueUnavailableException
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.UtilityFunctionOptimizer import UtilityFunctionOptimizer
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces import ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Spaces.HypergridAdapters import DiscreteToUnitContinuousHypergridAdapter
from mlos.Tracer import trace, traced


glow_worm_swarm_optimizer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="glow_worm_swarm_optimizer_config",
        dimensions=[
            DiscreteDimension(name="num_initial_points_multiplier", min=1, max=10),
            DiscreteDimension(name="num_worms", min=10, max=1000),
            DiscreteDimension(name="num_iterations", min=1, max=20), # TODO: consider other stopping criteria too
            ContinuousDimension(name="luciferin_decay_constant", min=0, max=1),
            ContinuousDimension(name="luciferin_enhancement_constant", min=0, max=1),
            ContinuousDimension(name="step_size", min=0, max=1),  # TODO: make this adaptive
            ContinuousDimension(name="initial_decision_radius", min=0, max=1, include_min=False),
            ContinuousDimension(name="max_sensory_radius", min=0.5, max=10), # TODO: add constraints
            DiscreteDimension(name="desired_num_neighbors", min=1, max=100),  # TODO: add constraint to make it smaller than num_worms
            ContinuousDimension(name="decision_radius_adjustment_constant", min=0, max=1)
        ]
    ),
    default=Point(
        num_initial_points_multiplier=5,
        num_worms=100,
        num_iterations=10,
        luciferin_decay_constant=0.2,
        luciferin_enhancement_constant=0.2,
        step_size=0.01,
        initial_decision_radius=0.2,
        max_sensory_radius=2,
        desired_num_neighbors=10,
        decision_radius_adjustment_constant=0.05
    )
)


class GlowWormSwarmOptimizer(UtilityFunctionOptimizer):
    """ Searches the utility function for maxima using glowworms.

    The first part of this has a good description:
        https://www.hindawi.com/journals/mpe/2016/5481602/

    The main benefits are:

        1. It doesn't require a gradient
        2. It is well parallelizeable (batchable)

    The main drawback is that it queries the utility function many times, and that's somewhat slow, but it would be
    cheap to optimize.

    """

    def __init__(
            self,
            optimizer_config: Point,
            optimization_problem: OptimizationProblem,
            utility_function: UtilityFunction,
            logger=None
    ):
        UtilityFunctionOptimizer.__init__(self, optimizer_config, optimization_problem, utility_function, logger)

        self.parameter_adapter = DiscreteToUnitContinuousHypergridAdapter(
            adaptee=self.optimization_problem.parameter_space
        )
        self.dimension_names = [dimension.name for dimension in self.parameter_adapter.dimensions]

    @trace()
    def suggest(self, context_values_dataframe=None):  # pylint: disable=unused-argument
        """ Returns the next best configuration to try.

        The idea is pretty simple:
            1. We start with a random population of glowworms, whose luciferin levels are equal to their utility function value.
            2. Each glowworm looks around for all other glowworms in its neighborhood and finds ones that are brighter.
            3. Each glowworm randomly selects from its brighter neighbors the one to walk towards (with probability proportional to the diff in brightness).
            4. Everybody takes a step.
            5. Everybody updates step size to have the desired number of neighbors.
            5. Update luciferin levels.


        """
        assert context_values_dataframe is None or len(context_values_dataframe.index) == 1

        # TODO: consider remembering great features from previous invocations of the suggest() method.
        parameters_df = self.optimization_problem.parameter_space.random_dataframe(
            num_samples=self.optimizer_config.num_worms * self.optimizer_config.num_initial_points_multiplier
        )

        features_df = self.optimization_problem.construct_feature_dataframe(
            parameters_df=parameters_df.copy(deep=False),
            context_df=context_values_dataframe,
            product=True
        )

        utility_function_values = self.utility_function(feature_values_pandas_frame=features_df.copy(deep=False))
        num_utility_function_values = len(utility_function_values.index)
        if num_utility_function_values == 0:
            raise UtilityValueUnavailableException(f"Utility function {self.utility_function.__class__.__name__} produced no values.")

        # TODO: keep getting configs until we have enough utility values to get started. Or assign 0 to missing ones,
        #  and let them climb out of their infeasible holes.
        top_utility_values = utility_function_values.nlargest(n=self.optimizer_config.num_worms, columns=['utility'])

        # TODO: could it be in place?
        params_for_top_utility = self.parameter_adapter.project_dataframe(parameters_df.loc[top_utility_values.index], in_place=False)
        worms = pd.concat([params_for_top_utility, top_utility_values], axis=1)
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
            worms = self.compute_utility(worms, context_values_dataframe)
            worms['luciferin'] = (1 - self.optimizer_config.luciferin_decay_constant) * worms['luciferin'] + \
                                 self.optimizer_config.luciferin_enhancement_constant * worms['utility']

        # TODO: return the max of all seen configs - not just the configs that the glowworms occupied in this iteration.
        idx_of_max = worms['utility'].idxmax()
        best_config = worms.loc[[idx_of_max], self.dimension_names]
        config_to_suggest = Point.from_dataframe(best_config)
        self.logger.debug(f"Suggesting: {str(config_to_suggest)}.")
        # TODO: we might have to go for second or nth best if the projection won't work out. But then again if we were
        # TODO: able to compute the utility function then the projection has worked out once before...
        return self.parameter_adapter.unproject_point(config_to_suggest)

    @trace()
    def compute_utility(self, worms, context_values_df):
        """ Computes utility function values for each worm.

        Since some worm positions will produce a NaN, we need to keep producing new utility values for those.

        :param worms:
        :return:
        """
        unprojected_params_df = self.parameter_adapter.unproject_dataframe(worms[self.dimension_names], in_place=False)
        features_df = self.optimization_problem.construct_feature_dataframe(unprojected_params_df, context_values_df, product=False)
        utility_function_values = self.utility_function(features_df.copy(deep=False))
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
