"""
Contains the BaseOptimizer abstract class.
"""

from abc import ABCMeta, abstractmethod

import ConfigSpace
import pandas as pd


class BaseOptimizer(metaclass=ABCMeta):
    """Optimizer abstract base class defining the basic interface.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.
    """
    def __init__(self, parameter_space: ConfigSpace.ConfigurationSpace):
        self.parameter_space: ConfigSpace.ConfigurationSpace = parameter_space
        self._observations = []
        self._pending_observations = []

    def __repr__(self):
        return f"{self.__class__.__name__}(parameter_space={self.parameter_space})"

    @abstractmethod
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
        pass    # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
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
        pass    # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
    def register_pending(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        """Registers the given configurations as "pending".
        That is it say, it has been suggested by the optimizer, and an experiment trial has been started.
        This can be useful for executing multiple trials in parallel, retry logic, etc.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        pass    # pylint: disable=unnecessary-pass # pragma: no cover

    def get_observations(self):
        """Returns the observations as a dataframe.

        Returns
        -------
        observations : pd.DataFrame
            Dataframe of observations. The columns are parameter names and "score" for the score, each row is an observation.
        """
        if len(self._observations) == 0:
            raise ValueError("No observations registered yet.")
        configs = pd.concat([config for config, _, _ in self._observations])
        scores = pd.concat([score for _, score, _ in self._observations])
        try:
            contexts = pd.concat([context for _, _, context in self._observations])
        except ValueError:
            contexts = None
        configs["score"] = scores
        if contexts is not None:
            # configs = pd.concat([configs, contexts], axis=1)
            # Not reachable for now
            raise NotImplementedError  # pragma: no cover
        return configs

    def get_best_observation(self):
        """Returns the best observation so far as a dataframe.

        Returns
        -------
        best_observation : pd.DataFrame
            Dataframe with a single row containing the best observation. The columns are parameter names and "score" for the score.
        """
        if len(self._observations) == 0:
            raise ValueError("No observations registered yet.")
        observations = self.get_observations()
        return observations.nsmallest(1, columns='score')
