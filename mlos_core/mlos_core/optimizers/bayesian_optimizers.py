"""
Contains the wrapper classes for different Bayesian optimizers.
"""

from abc import ABCMeta, abstractmethod

import ConfigSpace
import numpy as np
import pandas as pd

from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.spaces import configspace_to_skopt_space, configspace_to_emukit_space


class BaseBayesianOptimizer(BaseOptimizer, metaclass=ABCMeta):
    """Abstract base class defining the interface for Bayesian optimization. """
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
    """
    def __init__(self, parameter_space: ConfigSpace.ConfigurationSpace):
        super().__init__(parameter_space)
        self.emukit_parameter_space = configspace_to_emukit_space(parameter_space)
        self.gpbo = None

    def register(self, configurations: pd.DataFrame, scores: pd.Series, context: pd.DataFrame = None):
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
        self._observations.append((configurations, scores, context))
        if context is not None:
            # not sure how that works here?
            raise NotImplementedError
        if self.gpbo is None:
            # we're in the random initialization phase
            # just remembering the observation above is enough
            return
        results = []
        for (_, config), score in zip(configurations.iterrows(), scores):
            results.append(UserFunctionResult(config, np.array([score])))
        self.gpbo.loop_state.update(results)
        self.gpbo._update_models()  # pylint: disable=protected-access

    def suggest(self, context: pd.DataFrame = None):
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
        from emukit.examples.gp_bayesian_optimization.single_objective_bayesian_optimization import GPBayesianOptimization  # noqa pylint: disable=import-outside-toplevel
        if context is not None:
            raise NotImplementedError()
        if len(self._observations) <= 10:
            from emukit.core.initial_designs import RandomDesign    # pylint: disable=import-outside-toplevel
            config = RandomDesign(self.emukit_parameter_space).get_samples(1)
        else:
            if self.gpbo is None:
                # this should happen exactly once, when calling the 11th time
                observations = self.get_observations()
                self.gpbo = GPBayesianOptimization(
                    variables_list=self.emukit_parameter_space.parameters,
                    X=np.array(observations.drop(columns='score')),
                    Y=np.array(observations[['score']]))
            # this should happen any time after the initial model is created
            config = self.gpbo.get_next_points(results=[])
        return pd.DataFrame(config, columns=self.parameter_space.get_hyperparameter_names())

    def register_pending(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        raise NotImplementedError()

    def surrogate_predict(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        if context is not None:
            raise NotImplementedError
        # TODO return variance in some way
        # TODO check columns in configurations
        mean_predictions, variance_predictions = self.gpbo.model.predict(np.array(configurations))
        # make 2ndim array into column vector
        return mean_predictions.reshape(-1,)

    def acquisition_function(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        raise NotImplementedError()


class SkoptOptimizer(BaseBayesianOptimizer):
    """Wrapper class for Skopt based Bayesian optimization.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.
    """
    def __init__(self, parameter_space: ConfigSpace.ConfigurationSpace, base_estimator='gp'):
        from skopt import Optimizer as Optimizer_Skopt  # pylint: disable=import-outside-toplevel
        self.base_optimizer = Optimizer_Skopt(configspace_to_skopt_space(parameter_space), base_estimator=base_estimator)
        super().__init__(parameter_space)

    def register(self, configurations: pd.DataFrame, scores: pd.Series, context: pd.DataFrame = None):
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
        self._observations.append((configurations, scores, context))

        if context is not None:
            raise NotImplementedError
        self.base_optimizer.tell(np.array(configurations).tolist(), np.array(scores).tolist())

    def suggest(self, context: pd.DataFrame = None):
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
            raise NotImplementedError
        return pd.DataFrame([self.base_optimizer.ask()], columns=self.parameter_space.get_hyperparameter_names())

    def register_pending(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        raise NotImplementedError()

    def surrogate_predict(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        if context is not None:
            raise NotImplementedError
        # TODO check configuration columns
        return self.base_optimizer.models[-1].predict(np.array(configurations))

    def acquisition_function(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        # This seems actually non-trivial to get out of skopt, so maybe we actually shouldn't implement this.
        raise NotImplementedError()
