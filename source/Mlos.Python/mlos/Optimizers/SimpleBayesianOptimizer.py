# pylint: disable=protected-access
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

import pickle

import numpy as np
from bayes_opt import BayesianOptimization, UtilityFunction

from mlos.Spaces import CategoricalDimension, ContinuousDimension, Dimension, DiscreteDimension, SimpleHypergrid, Point, DefaultConfigMeta
from .OptimizationProblem import OptimizationProblem
from .OptimizerInterface import OptimizerInterface


class SimpleBayesianOptimizerConfig(metaclass=DefaultConfigMeta):

    CONFIG_SPACE = SimpleHypergrid(
        name="SimpleBayesianOptimizerConfig",
        dimensions=[
            CategoricalDimension(name='utility_function', values=['ucb', 'ei', 'poi']),
            ContinuousDimension(name='kappa', min=-5, max=5),
            ContinuousDimension(name='xi', min=-5, max=5)
        ]
    )

    _DEFAULT = Point(
        utility_function='ucb',
        kappa=3,
        xi=1
    )

    @classmethod
    def contains(cls, config):
        if not isinstance(config, cls):
            return False

        return Point(
            utility_function=config.utility_function,
            kappa=config.kappa,
            xi=config.xi
        ) in cls.CONFIG_SPACE

    @classmethod
    def create_from_config_point(cls, config_point):
        assert config_point in cls.CONFIG_SPACE
        return cls(
            utility_function=config_point.utility_function,
            kappa=config_point.kappa,
            xi=config_point.xi
        )

    def __init__(
            self,
            utility_function=None,
            kappa=None,
            xi=None
    ):
        if utility_function is None:
            utility_function = self._DEFAULT.utility_function
        if kappa is None:
            kappa = self._DEFAULT.kappa
        if xi is None:
            xi = self._DEFAULT.xi

        self.utility_function = utility_function
        self.kappa = kappa
        self.xi = xi

    def to_dict(self):
        return {
            'utility_function': self.utility_function,
            'kappa': self.kappa,
            'xi': self.xi
        }


class SimpleBayesianOptimizer(OptimizerInterface):
    """ A toy bayesian optimizer based on Gaussian processes.

    """

    def __init__(self, optimization_problem: OptimizationProblem, optimizer_config: SimpleBayesianOptimizerConfig):
        assert len(optimization_problem.objectives) == 1, "This is a single-objective optimizer."
        OptimizerInterface.__init__(self, optimization_problem)
        self.minimize = self.optimization_problem.objectives[0].minimize

        self._ordered_parameter_names = [
            dimension.name
            for dimension
            in self.optimization_problem.parameter_space.dimensions
            if dimension.name not in OptimizationProblem.META_DIMENSION_NAMES
        ]

        self._ordered_feature_names = [
            dimension.name
            for dimension
            in self.optimization_problem.feature_space.dimensions
            if dimension.name not in OptimizationProblem.META_DIMENSION_NAMES
        ]

        assert SimpleBayesianOptimizerConfig.contains(optimizer_config)
        self._optimizer_config = optimizer_config
        self._utility_function = UtilityFunction(
            kind=self._optimizer_config.utility_function,
            kappa=self._optimizer_config.kappa,
            xi=self._optimizer_config.xi
        )

        self._full_parameter_space_bounds = self._format_search_space(self.optimization_problem.parameter_space)
        self._full_feature_space_bounds = self._format_search_space(self.optimization_problem.feature_space)

        self._optimizer = BayesianOptimization(
            f=None,
            pbounds=self._full_feature_space_bounds  # Both parameters and context are used for regression.
        )


        # Optionally the optimizer can focus on a subspace of the parameter search space.
        #
        self.focused = False
        self._focused_parameter_space = None
        self._focused_parameter_space_bounds = None

        # HISTORY
        self._registered_param_combos = []
        self._observations = []
        self._models = []

    @property
    def parameter_space(self):
        return self.optimization_problem.parameter_space

    @property
    def feature_space(self):
        return self.optimization_problem.feature_space

    @property
    def current_search_space(self):
        if self.focused:
            return self._focused_parameter_space
        return self.optimization_problem.parameter_space

    @property
    def observations(self):
        return self._observations

    def get_all_observations(self):
        return None

    def get_optimizer_convergence_state(self):
        return None

    def suggest(self, random=False, context=None):  # pylint: disable=redefined-outer-name,unused-argument

        suggested_params = None

        if random:
            suggested_params = self.current_search_space.random().to_dict()

        else:
            if not self.focused:
                self._optimizer._space._bounds = self._format_parameter_bounds(self._full_parameter_space_bounds)
            else:
                self._optimizer._space._bounds = self._format_parameter_bounds(self._focused_parameter_space_bounds)
            suggested_params = self._optimizer.suggest(utility_function=self._utility_function)

            for param_name, param_value in suggested_params.items():
                param_dimension = self.feature_space[param_name]
                if isinstance(param_dimension, DiscreteDimension):
                    # we need to round the parameter
                    suggested_params[param_name] = int(round(param_value))
                elif isinstance(param_dimension, CategoricalDimension):
                    # we need to round and index into the dimension
                    suggested_params[param_name] = param_dimension[int(round(param_value))]

            # we also have to remove the parameter root grid name
            param_names = [param_name for param_name in suggested_params.keys()]
            for param_name in param_names:
                _, param_name_without_subgrid_name = Dimension.split_dimension_name(param_name)
                suggested_params[param_name_without_subgrid_name] = suggested_params[param_name]
                del suggested_params[param_name]

            retries_remaining = 100
            while retries_remaining > 0 and (suggested_params in self._registered_param_combos):
                suggested_params = self.current_search_space.random().to_dict()
                retries_remaining -= 1

        assert Point(**suggested_params) in self.parameter_space
        return suggested_params

    def register(self, params, target_value): # pylint: disable=arguments-differ
        # TODO: make this conform to the OptimizerInterface

        if params in self._registered_param_combos:
            return
        self._optimizer._space._bounds = self._format_parameter_bounds(self._full_feature_space_bounds)
        self._optimizer.register(
            params=params,
            target=-target_value if self.minimize else target_value
        )

        self._registered_param_combos.append(params)
        self._observations.append({'params': params, 'target': target_value})
        self._models.append(pickle.dumps(self._optimizer))

    def _named_params_to_params(self, named_params):
        return [named_params[dimension.name] for dimension in self.feature_space.dimensions]

    def predict(self, feature_values_pandas_frame, t=None):

        params = feature_values_pandas_frame[self._ordered_feature_names].to_numpy()
        if t is None:
            self._optimizer._space._bounds = self._format_parameter_bounds(self._full_feature_space_bounds)
            mean, stdev = self._optimizer._gp.predict(params, return_std=True)
            if self.minimize:
                mean = -mean
            return mean, stdev

        # We are asked to predict what the optimizer believed at time t
        assert 0 <= t < len(self._observations)
        optimizer = pickle.loads(self._models[t])
        mean, stdev = optimizer._gp.predict(params, return_std=True)
        if self.minimize:
            mean = -mean
        return mean, stdev

    def estimate_local_parameter_importance(self, params, t=None):
        """ Estimates local parameter importance by querying the model for predictions in the neighborhood of params.

        :param params:
        :param t:
        :return: A dictionary with the following form: {
            'predicted_mean': 0.0,
            'predicted_stdev': 1.0,

            'first_dimension_name': {
                'delta': 1,
                'increase': {
                    'predicted_target': 2.0,
                    'predicted_target_stdev': 1.0
                },
                'decrease': {
                    'predicted_target': None,
                    'predicted_target_stdev': None
                }
            },
            'second_dimension_name': {
                'delta': 1,
                'increase': {
                    'predicted_target': 2.0,
                    'predicted_target_stdev': 1.0
                },
                'decrease': {
                    'predicted_target': None,
                    'predicted_target_stdev': None
                }
            }
        }
        """

        predicted_target, predicted_target_stdev = self.predict([params], t=t)
        predicted_target, predicted_target_stdev = predicted_target[0], predicted_target_stdev[0]
        local_parameter_importance = {
            'predicted_target': predicted_target,
            'predicted_target_stdev': predicted_target_stdev
        }

        for i, param_value in enumerate(params):
            param_dimension = self.parameter_space.dimensions[i]
            assert isinstance(param_dimension, DiscreteDimension), "Local parameter importance estimates are currently only implemented for Discrete Dimensions"

            param_delta = param_dimension.stride

            predictions_in_neighborhood = {
                'delta': param_delta
            }

            for direction, delta in [('increase', param_delta), ('decrease', -param_delta)]:
                target_after_change, target_after_change_stdev = None, None
                predicted_target_delta = None
                predicted_percentage_target_delta = None

                if param_dimension.min <= param_value + delta <= param_dimension.max:
                    new_params = [value for value in params]
                    new_params[i] += delta
                    target_after_change, target_after_change_stdev = self.predict([new_params], t=t)
                    target_after_change = target_after_change[0]
                    target_after_change_stdev = target_after_change_stdev[0]
                    predicted_target_delta = target_after_change - predicted_target
                    predicted_percentage_target_delta = (predicted_target_delta*100.0/predicted_target)
                predictions_in_neighborhood[direction] = {
                    'predicted_target': target_after_change,
                    'predicted_target_stdev': target_after_change_stdev,
                    'predicted_target_delta': predicted_target_delta,
                    'predicted_percentage_target_delta': predicted_percentage_target_delta
                }
            local_parameter_importance[param_dimension.name] = predictions_in_neighborhood

        return local_parameter_importance

    def optimum(self, stay_focused=False):
        # TODO: add arguments to set context
        self._optimizer._space._bounds = self._full_feature_space_bounds

        if stay_focused and self.focused:
            self._optimizer._space._bounds = self._format_parameter_bounds(self._focused_parameter_space_bounds)

        optimal_config_and_target = self._optimizer.max
        if self.minimize:
            optimal_config_and_target['target'] = -optimal_config_and_target['target']
        return optimal_config_and_target

    def focus(self, subspace):
        assert subspace in self.parameter_space
        parameter_bounds = self._format_search_space(subspace)
        self._focused_parameter_space = subspace
        self._focused_parameter_space_bounds = parameter_bounds
        self.focused = True

    def reset_focus(self):
        self._focused_parameter_space_bounds = None
        self._focused_parameter_space = None
        self.focused = False

    @staticmethod
    def _format_search_space(search_space):
        """ Formats the feature_space Hypergrid to the match the optimizer's api.

        In this case the optimizer expects a dictionary with a (min, max) values tuple.

        :return:
        """
        parameter_bounds = {}
        for dimension in search_space.dimensions:
            if dimension.name in OptimizationProblem.META_DIMENSION_NAMES:
                continue
            if isinstance(dimension, (ContinuousDimension, DiscreteDimension)):
                parameter_bounds[dimension.name] = (dimension.min, dimension.max)
            else:
                parameter_bounds[dimension.name] = (0, len(dimension) - 1)

        return parameter_bounds

    def _format_parameter_bounds(self, parameter_bounds):
        """ Formats parameter bounds for consumption by GaussianProcessRegressor.

        The regressor expects a numpy array where each row (along the 0th dimension) contains two columns:
        min and max. The array is meant to be sorted alphabetically.

        :param parameter_bounds:
        :return:
        """
        bounds_array_ordered_by_feature_name = []

        for feature_name in sorted(self._ordered_feature_names):
            if feature_name in parameter_bounds.keys():
                bounds_array_ordered_by_feature_name.append(parameter_bounds[feature_name])
            else:
                bounds_array_ordered_by_feature_name.append(self._full_feature_space_bounds[feature_name])

        return np.array(bounds_array_ordered_by_feature_name)
