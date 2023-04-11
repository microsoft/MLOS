#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper classes for different Bayesian optimizers.
"""

from typing import Optional
from abc import ABCMeta, abstractmethod

import ConfigSpace
import numpy as np
import numpy.typing as npt
import pandas as pd

from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter
from mlos_core.spaces import configspace_to_skopt_space, configspace_to_emukit_space


class BaseBayesianOptimizer(BaseOptimizer, metaclass=ABCMeta):
    """Abstract base class defining the interface for Bayesian optimization."""

    @abstractmethod
    def surrogate_predict(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        """Obtain a prediction from this Bayesian optimizer's surrogate model for the given configuration(s).

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        pass    # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
    def acquisition_function(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        """Invokes the acquisition function from this Bayesian optimizer for the given configuration.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        pass    # pylint: disable=unnecessary-pass # pragma: no cover


class EmukitOptimizer(BaseBayesianOptimizer):
    """Wrapper class for Emukit based Bayesian optimization.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.

    space_adapter : BaseSpaceAdapter
        The space adapter class to employ for parameter space transformations.
    """

    def __init__(self, parameter_space: ConfigSpace.ConfigurationSpace, space_adapter: Optional[BaseSpaceAdapter] = None):
        super().__init__(parameter_space, space_adapter)
        self.emukit_parameter_space = configspace_to_emukit_space(self.optimizer_parameter_space)
        from emukit.examples.gp_bayesian_optimization.single_objective_bayesian_optimization import GPBayesianOptimization  # noqa pylint: disable=import-outside-toplevel
        self.gpbo: GPBayesianOptimization

    def _register(self, configurations: pd.DataFrame, scores: pd.Series, context: pd.DataFrame = None):
        """Registers the given configurations and scores.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        scores : pd.Series
            Scores from running the configurations. The index is the same as the index of the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        from emukit.core.loop.user_function_result import UserFunctionResult    # pylint: disable=import-outside-toplevel
        if context is not None:
            # not sure how that works here?
            raise NotImplementedError()
        if getattr(self, 'gpbo', None) is None:
            # we're in the random initialization phase
            # just remembering the observation above is enough
            return
        results = []
        for (_, config), score in zip(configurations.iterrows(), scores):
            one_hot = self._to_1hot(pd.DataFrame([config]))
            results.append(UserFunctionResult(one_hot[0], np.array([score])))
        self.gpbo.loop_state.update(results)
        self.gpbo._update_models()  # pylint: disable=protected-access

    def _suggest(self, context: pd.DataFrame = None):
        """Suggests a new configuration.

        Parameters
        ----------
        context : pd.DataFrame
            Not Yet Implemented.

        Returns
        -------
        configuration : pd.DataFrame
            Pandas dataframe with a single row. Column names are the parameter names.
        """
        if context is not None:
            raise NotImplementedError()
        if len(self._observations) <= 10:
            from emukit.core.initial_designs import RandomDesign    # pylint: disable=import-outside-toplevel
            config = RandomDesign(self.emukit_parameter_space).get_samples(1)
        else:
            if getattr(self, 'gpbo', None) is None:
                # this should happen exactly once, when calling the 11th time
                self._initialize_optimizer()
            # this should happen any time after the initial model is created
            config = self.gpbo.get_next_points(results=[])
        return self._from_1hot(config)

    def register_pending(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        raise NotImplementedError()

    def surrogate_predict(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        if context is not None:
            raise NotImplementedError()
        if self.space_adapter is not None:
            raise NotImplementedError()
        # TODO return variance in some way
        if self._space_adapter:
            configurations = self._space_adapter.inverse_transform(configurations)
        one_hot = self._to_1hot(configurations)
        mean_predictions, _variance_predictions = self.gpbo.model.predict(one_hot)
        # make 2ndim array into column vector
        return mean_predictions.reshape(-1,)

    def acquisition_function(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        raise NotImplementedError()

    def _initialize_optimizer(self):
        """Bootstrap a new Emukit optimizer on the initial observations."""
        from emukit.examples.gp_bayesian_optimization.single_objective_bayesian_optimization import GPBayesianOptimization  # noqa pylint: disable=import-outside-toplevel
        observations = self.get_observations()

        initial_input = observations.drop(columns='score')
        initial_output = observations[['score']]

        if self.space_adapter is not None:
            initial_input = self.space_adapter.inverse_transform(initial_input)

        self.gpbo = GPBayesianOptimization(
            variables_list=self.emukit_parameter_space.parameters,
            X=self._to_1hot(initial_input),
            Y=np.array(initial_output)
        )


class SkoptOptimizer(BaseBayesianOptimizer):
    """Wrapper class for Skopt based Bayesian optimization.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.
    """

    def __init__(
        self,
        parameter_space: ConfigSpace.ConfigurationSpace,
        space_adapter: Optional[BaseSpaceAdapter] = None,
        base_estimator: str = 'gp',
        seed: Optional[int] = None,
    ):
        super().__init__(parameter_space, space_adapter)

        from skopt import Optimizer as Optimizer_Skopt  # pylint: disable=import-outside-toplevel
        self.base_optimizer = Optimizer_Skopt(
            configspace_to_skopt_space(self.optimizer_parameter_space),
            base_estimator=base_estimator,
            random_state=seed,
        )
        if base_estimator == 'et':
            self._transform = self._to_1hot
        elif base_estimator == 'gp':
            self._transform = self._to_numeric
        else:
            self._transform = np.array

    def _to_numeric(self, config: pd.DataFrame) -> npt.NDArray:
        """
        Convert categorical values in the DataFrame to ordinal integers and return a numpy array.
        This transformation is necessary for the Gaussian Process based optimizer.

        Parameters
        ----------
        config : pd.DataFrame
            Dataframe of configurations / parameters.
            The columns are parameter names and the rows are the configurations.

        Returns
        -------
        config : np.array
            Numpy array of floats with all categoricals replaced with their ordinal numbers.
        """
        config = config.copy()
        for param in self.optimizer_parameter_space.get_hyperparameters():
            if isinstance(param, ConfigSpace.CategoricalHyperparameter):
                config[param.name] = config[param.name].apply(param.choices.index)
        return config.to_numpy(dtype=np.float32)

    def _register(self, configurations: pd.DataFrame, scores: pd.Series, context: pd.DataFrame = None):
        """Registers the given configurations and scores.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        scores : pd.Series
            Scores from running the configurations. The index is the same as the index of the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        if context is not None:
            raise NotImplementedError()
        # DataFrame columns must be in the same order
        # as the hyperparameters in the config space:
        param_names = self.optimizer_parameter_space.get_hyperparameter_names()
        data = configurations[param_names].to_numpy().tolist()
        self.base_optimizer.tell(data, scores.to_list())

    def _suggest(self, context: pd.DataFrame = None):
        """Suggests a new configuration.

        Parameters
        ----------
        context : pd.DataFrame
            Not Yet Implemented.

        Returns
        -------
        configuration : pd.DataFrame
            Pandas dataframe with a single row. Column names are the parameter names.
        """
        if context is not None:
            raise NotImplementedError()
        return pd.DataFrame([self.base_optimizer.ask()], columns=self.optimizer_parameter_space.get_hyperparameter_names())

    def register_pending(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        raise NotImplementedError()

    def surrogate_predict(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        if context is not None:
            raise NotImplementedError()
        if self.space_adapter is not None:
            raise NotImplementedError()
        return self.base_optimizer.models[-1].predict(self._transform(configurations))

    def acquisition_function(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        # This seems actually non-trivial to get out of skopt, so maybe we actually shouldn't implement this.
        raise NotImplementedError()
