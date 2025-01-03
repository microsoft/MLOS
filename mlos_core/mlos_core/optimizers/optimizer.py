#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Contains the :py:class:`.BaseOptimizer` abstract class."""

import collections
from abc import ABCMeta, abstractmethod
from copy import deepcopy

import ConfigSpace
import numpy as np
import numpy.typing as npt
import pandas as pd

from mlos_core.data_classes import Observation, Observations, Suggestion
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter
from mlos_core.util import config_to_series


class BaseOptimizer(metaclass=ABCMeta):
    """Optimizer abstract base class defining the basic interface:
    :py:meth:`~.BaseOptimizer.suggest`,
    :py:meth:`~.BaseOptimizer.register`,
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        *,
        parameter_space: ConfigSpace.ConfigurationSpace,
        optimization_targets: list[str],
        objective_weights: list[float] | None = None,
        space_adapter: BaseSpaceAdapter | None = None,
    ):
        """
        Create a new instance of the base optimizer.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            The parameter space to optimize.
        optimization_targets : list[str]
            The names of the optimization targets to minimize.
            To maximize a target, use the negative of the target when registering scores.
        objective_weights : Optional[list[float]]
            Optional list of weights of optimization targets.
        space_adapter : BaseSpaceAdapter
            The space adapter class to employ for parameter space transformations.
        """
        self.parameter_space: ConfigSpace.ConfigurationSpace = parameter_space
        """The parameter space to optimize."""

        self.optimizer_parameter_space: ConfigSpace.ConfigurationSpace = (
            parameter_space if space_adapter is None else space_adapter.target_parameter_space
        )
        """
        The parameter space actually used by the optimizer.

        (in case a :py:mod:`SpaceAdapter <mlos_core.spaces.adapters>` is used)
        """

        if space_adapter is not None and space_adapter.orig_parameter_space != parameter_space:
            raise ValueError("Given parameter space differs from the one given to space adapter")

        self._optimization_targets = optimization_targets
        self._objective_weights = objective_weights
        if objective_weights is not None and len(objective_weights) != len(optimization_targets):
            raise ValueError("Number of weights must match the number of optimization targets")

        self._space_adapter: BaseSpaceAdapter | None = space_adapter
        self._observations: Observations = Observations()
        self._has_context: bool | None = None
        self._pending_observations: list[tuple[pd.DataFrame, pd.DataFrame | None]] = []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(space_adapter={self.space_adapter})"

    @property
    def space_adapter(self) -> BaseSpaceAdapter | None:
        """Get the space adapter instance (if any)."""
        return self._space_adapter

    def register(
        self,
        observations: Observation | Observations,
    ) -> None:
        """
        Register all observations at once. Exactly one of observations or observation
        must be provided.

        Parameters
        ----------
        observations: Optional[Union[Observation, Observations]]
            The observations to register.
        """
        if isinstance(observations, Observation):
            observations = Observations(observations=[observations])
        # Check input and transform the observations if a space adapter is present.
        observations = Observations(
            observations=[
                self._preprocess_observation(observation) for observation in observations
            ]
        )
        # Now bulk register all observations (details delegated to the underlying classes).
        self._register(observations)

    def _preprocess_observation(self, observation: Observation) -> Observation:
        """
        Wrapper method, which employs the space adapter (if any), and does some input
        validation, before registering the configs and scores.

        Parameters
        ----------
        observation: Observation
            The observation to register.

        Returns
        -------
        observation: Observation
            The (possibly transformed) observation to register.
        """
        # Do some input validation.
        assert observation.metadata is None or isinstance(observation.metadata, pd.Series)
        assert set(observation.score.index) == set(
            self._optimization_targets
        ), "Mismatched optimization targets."
        assert self._has_context is None or self._has_context ^ (
            observation.context is None
        ), "Context must always be added or never be added."
        assert len(observation.config) == len(
            self.parameter_space.values()
        ), "Mismatched configuration shape."

        self._has_context = observation.context is not None
        self._observations.append(observation)

        transformed_observation = deepcopy(observation)  # Needed to support named tuples
        if self._space_adapter:
            transformed_observation = Observation(
                config=self._space_adapter.inverse_transform(transformed_observation.config),
                score=transformed_observation.score,
                context=transformed_observation.context,
                metadata=transformed_observation.metadata,
            )
            assert len(transformed_observation.config) == len(
                self.optimizer_parameter_space.values()
            ), "Mismatched configuration shape after inverse transform."
        return transformed_observation

    @abstractmethod
    def _register(
        self,
        observations: Observations,
    ) -> None:
        """
        Registers the given configs and scores.

        Parameters
        ----------
        observations: Observations
            The set of observations to register.
        """
        pass  # pylint: disable=unnecessary-pass # pragma: no cover

    def suggest(
        self,
        *,
        context: pd.Series | None = None,
        defaults: bool = False,
    ) -> Suggestion:
        """
        Wrapper method, which employs the space adapter (if any), after suggesting a new
        configuration.

        Parameters
        ----------
        context : pandas.Series
            Not Yet Implemented.
        defaults : bool
            Whether or not to return the default config instead of an optimizer guided one.
            By default, use the one from the optimizer.

        Returns
        -------
        suggestion: Suggestion
            The suggested point to evaluate.
        """
        if defaults:
            configuration = config_to_series(self.parameter_space.get_default_configuration())
            if self.space_adapter is not None:
                configuration = self.space_adapter.inverse_transform(configuration)
            suggestion = Suggestion(config=configuration, context=context, metadata=None)
        else:
            suggestion = self._suggest(context=context)
            assert set(suggestion.config.index).issubset(set(self.optimizer_parameter_space)), (
                "Optimizer suggested a configuration that does "
                "not match the expected parameter space."
            )
        if self._space_adapter:
            suggestion = Suggestion(
                config=self._space_adapter.transform(suggestion.config),
                context=suggestion.context,
                metadata=suggestion.metadata,
            )
            assert set(suggestion.config.index).issubset(set(self.parameter_space)), (
                "Space adapter produced a configuration that does "
                "not match the expected parameter space."
            )
        return suggestion

    @abstractmethod
    def _suggest(
        self,
        *,
        context: pd.Series | None = None,
    ) -> Suggestion:
        """
        Suggests a new configuration.

        Parameters
        ----------
        context : pandas.Series
            Not Yet Implemented.

        Returns
        -------
        suggestion: Suggestion
            The suggestion to evaluate.
        """
        pass  # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
    def register_pending(self, pending: Suggestion) -> None:
        """
        Registers the given suggestion as "pending". That is it say, it has been
        suggested by the optimizer, and an experiment trial has been started. This can
        be useful for executing multiple trials in parallel, retry logic, etc.

        Parameters
        ----------
        pending: Suggestion
            The pending suggestion to register.
        """
        pass  # pylint: disable=unnecessary-pass # pragma: no cover

    def get_observations(self) -> Observations:
        """
        Returns the observations as a triplet of DataFrames (config, score, context).

        Returns
        -------
        observations : Observations
            All the observations registered so far.
        """
        if len(self._observations) == 0:
            raise ValueError("No observations registered yet.")
        return self._observations

    def get_best_observations(
        self,
        n_max: int = 1,
    ) -> Observations:
        """
        Get the N best observations so far as a filtered version of Observations.
        Default is N=1. The columns are ordered in ASCENDING order of the optimization
        targets. The function uses `pandas.DataFrame.nsmallest(..., keep="first")`
        method under the hood.

        Parameters
        ----------
        n_max : int
            Maximum number of best observations to return. Default is 1.

        Returns
        -------
        observations : Observations
            A filtered version of Observations with the best N observations.
        """
        observations = self.get_observations()
        if len(observations) == 0:
            raise ValueError("No observations registered yet.")

        idx = observations.scores.nsmallest(
            n_max,
            columns=self._optimization_targets,
            keep="first",
        ).index
        return observations.filter_by_index(idx)

    def cleanup(self) -> None:
        """
        Remove temp files, release resources, etc.

        after use. Default is no-op. Redefine this method in optimizers that require
        cleanup.
        """

    def _from_1hot(self, config: npt.NDArray) -> pd.DataFrame:
        """Convert numpy array from one-hot encoding to a DataFrame with categoricals
        and ints in proper columns.
        """
        df_dict = collections.defaultdict(list)
        for i in range(config.shape[0]):
            j = 0
            for param in self.optimizer_parameter_space.values():
                if isinstance(param, ConfigSpace.CategoricalHyperparameter):
                    for offset, val in enumerate(param.choices):
                        if config[i][j + offset] == 1:
                            df_dict[param.name].append(val)
                            break
                    j += len(param.choices)
                else:
                    val = config[i][j]
                    if isinstance(param, ConfigSpace.UniformIntegerHyperparameter):
                        val = int(val)
                    df_dict[param.name].append(val)
                    j += 1
        return pd.DataFrame(df_dict)

    def _to_1hot(self, config: pd.DataFrame | pd.Series) -> npt.NDArray:
        """Convert pandas DataFrame to one-hot-encoded numpy array."""
        n_cols = 0
        n_rows = config.shape[0] if config.ndim > 1 else 1
        for param in self.optimizer_parameter_space.values():
            if isinstance(param, ConfigSpace.CategoricalHyperparameter):
                n_cols += len(param.choices)
            else:
                n_cols += 1
        one_hot = np.zeros((n_rows, n_cols), dtype=np.float32)
        for i in range(n_rows):
            j = 0
            for param in self.optimizer_parameter_space.values():
                if config.ndim > 1:
                    assert isinstance(config, pd.DataFrame)
                    col = config.columns.get_loc(param.name)
                    assert isinstance(col, int)
                    val = config.iloc[i, col]
                else:
                    assert isinstance(config, pd.Series)
                    col = config.index.get_loc(param.name)
                    assert isinstance(col, int)
                    val = config.iloc[col]
                if isinstance(param, ConfigSpace.CategoricalHyperparameter):
                    offset = param.choices.index(val)
                    one_hot[i][j + offset] = 1
                    j += len(param.choices)
                else:
                    one_hot[i][j] = val
                    j += 1
        return one_hot
