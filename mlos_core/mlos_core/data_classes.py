#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Data classes for ``mlos_core`` used to pass around configurations, observations, and
suggestions.

``mlos_core`` uses :external:py:mod:`pandas` :external:py:class:`~pandas.DataFrame`
s and :external:py:class:`~pandas.Series` to represent configurations and scores and
context (information about where the configuration was evaluated).

These modules encapsulate tuples of those for easier passing around and manipulation.
"""
from collections.abc import Iterable, Iterator
from typing import Any

import pandas as pd
from ConfigSpace import Configuration, ConfigurationSpace

from mlos_core.util import compare_optional_dataframe, compare_optional_series


class Observation:
    """A single observation of a configuration."""

    def __init__(
        self,
        *,
        config: pd.Series,
        score: pd.Series = pd.Series(),
        context: pd.Series | None = None,
        metadata: pd.Series | None = None,
    ):
        """
        Creates a new Observation object.

        Parameters
        ----------
        config : pandas.Series
            The configuration observed.
        score : pandas.Series
            The score metrics observed.
        context : pandas.Series | None
            The context in which the configuration was evaluated.
            Not Yet Implemented.
        metadata: pandas.Series | None
            The metadata in which the configuration was evaluated
        """
        self._config = config
        self._score = score
        self._context = context
        self._metadata = metadata

    @property
    def config(self) -> pd.Series:
        """Gets (a copy of) the config of the Observation."""
        return self._config.copy()

    @property
    def score(self) -> pd.Series:
        """Gets (a copy of) the score of the Observation."""
        return self._score.copy()

    @property
    def context(self) -> pd.Series | None:
        """Gets (a copy of) the context of the Observation."""
        return self._context.copy() if self._context is not None else None

    @property
    def metadata(self) -> pd.Series | None:
        """Gets (a copy of) the metadata of the Observation."""
        return self._metadata.copy() if self._metadata is not None else None

    def to_suggestion(self) -> "Suggestion":
        """
        Converts the observation to a suggestion.

        Returns
        -------
        Suggestion
            The suggestion.
        """
        return Suggestion(
            config=self.config,
            context=self.context,
            metadata=self.metadata,
        )

    def __repr__(self) -> str:
        return (
            f"Observation(config={self._config}, score={self._score}, "
            f"context={self._context}, metadata={self._metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Observation):
            return False

        if not self._config.equals(other._config):
            return False
        if not self._score.equals(other._score):
            return False
        if not compare_optional_series(self._context, other._context):
            return False
        if not compare_optional_series(self._metadata, other._metadata):
            return False

        return True

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


class Observations:
    """A set of observations of a configuration scores."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        configs: pd.DataFrame = pd.DataFrame(),
        scores: pd.DataFrame = pd.DataFrame(),
        contexts: pd.DataFrame | None = None,
        metadata: pd.DataFrame | None = None,
        observations: Iterable[Observation] | None = None,
    ):
        """
        Creates a new Observation object.

        Can accept either a set of Observations or a collection of aligned config and
        score (and optionally context) dataframes.

        If both are provided the two sets will be merged.

        Parameters
        ----------
        configs : pandas.DataFrame
            Pandas dataframe containing configurations. Column names are the parameter names.
        scores : pandas.DataFrame
            The score metrics observed in a dataframe.
        contexts : pandas.DataFrame | None
            The context in which the configuration was evaluated.
            Not Yet Implemented.
        metadata: pandas.DataFrame | None
            The metadata in which the configuration was evaluated
            Not Yet Implemented.
        """
        if observations is None:
            observations = []
        if any(observations):
            configs = pd.concat([obs.config.to_frame().T for obs in observations])
            scores = pd.concat([obs.score.to_frame().T for obs in observations])

            if sum(obs.context is None for obs in observations) == 0:
                contexts = pd.concat(
                    [obs.context.to_frame().T for obs in observations]  # type: ignore[union-attr]
                )
            else:
                contexts = None
            if sum(obs.metadata is None for obs in observations) == 0:
                metadata = pd.concat(
                    [obs.metadata.to_frame().T for obs in observations]  # type: ignore[union-attr]
                )
            else:
                metadata = None
        assert len(configs.index) == len(
            scores.index
        ), "config and score must have the same length"
        if contexts is not None:
            assert len(configs.index) == len(
                contexts.index
            ), "config and context must have the same length"
        if metadata is not None:
            assert len(configs.index) == len(
                metadata.index
            ), "config and metadata must have the same length"
        self._configs = configs.reset_index(drop=True)
        self._scores = scores.reset_index(drop=True)
        self._contexts = None if contexts is None else contexts.reset_index(drop=True)
        self._metadata = None if metadata is None else metadata.reset_index(drop=True)

    @property
    def configs(self) -> pd.DataFrame:
        """Gets a copy of the configs of the Observations."""
        return self._configs.copy()

    @property
    def scores(self) -> pd.DataFrame:
        """Gets a copy of the scores of the Observations."""
        return self._scores.copy()

    @property
    def contexts(self) -> pd.DataFrame | None:
        """Gets a copy of the contexts of the Observations."""
        return self._contexts.copy() if self._contexts is not None else None

    @property
    def metadata(self) -> pd.DataFrame | None:
        """Gets a copy of the metadata of the Observations."""
        return self._metadata.copy() if self._metadata is not None else None

    def filter_by_index(self, index: pd.Index) -> "Observations":
        """
        Filters the observation by the given indices.

        Parameters
        ----------
        index : pandas.Index
            The indices to filter by.

        Returns
        -------
        Observation
            The filtered observation.
        """
        return Observations(
            configs=self._configs.loc[index].copy(),
            scores=self._scores.loc[index].copy(),
            contexts=None if self._contexts is None else self._contexts.loc[index].copy(),
            metadata=None if self._metadata is None else self._metadata.loc[index].copy(),
        )

    def append(self, observation: Observation) -> None:
        """
        Appends the given observation to this observation.

        Parameters
        ----------
        observation : Observation
            The observation to append.
        """
        config = observation.config.to_frame().T
        score = observation.score.to_frame().T
        context = None if observation.context is None else observation.context.to_frame().T
        metadata = None if observation.metadata is None else observation.metadata.to_frame().T
        if len(self._configs.index) == 0:
            self._configs = config
            self._scores = score
            self._contexts = context
            self._metadata = metadata
            assert set(self.configs.index) == set(
                self.scores.index
            ), "config and score must have the same index"
            return

        self._configs = pd.concat([self._configs, config]).reset_index(drop=True)
        self._scores = pd.concat([self._scores, score]).reset_index(drop=True)
        assert set(self.configs.index) == set(
            self.scores.index
        ), "config and score must have the same index"

        if self._contexts is not None:
            assert context is not None, (
                "context of appending observation must not be null "
                "if context of prior observation is not null"
            )
            self._contexts = pd.concat([self._contexts, context]).reset_index(drop=True)
            assert self._configs.index.equals(
                self._contexts.index
            ), "config and context must have the same index"
        else:
            assert context is None, (
                "context of appending observation must be null "
                "if context of prior observation is null"
            )
        if self._metadata is not None:
            assert metadata is not None, (
                "context of appending observation must not be null "
                "if metadata of prior observation is not null"
            )
            self._metadata = pd.concat([self._metadata, metadata]).reset_index(drop=True)
            assert self._configs.index.equals(
                self._metadata.index
            ), "config and metadata must have the same index"
        else:
            assert metadata is None, (
                "context of appending observation must be null "
                "if metadata of prior observation is null"
            )

    def __len__(self) -> int:
        return len(self._configs.index)

    def __iter__(self) -> Iterator["Observation"]:
        for idx in self._configs.index:
            yield Observation(
                config=self._configs.loc[idx],
                score=self._scores.loc[idx],
                context=None if self._contexts is None else self._contexts.loc[idx],
                metadata=None if self._metadata is None else self._metadata.loc[idx],
            )

    def __repr__(self) -> str:
        return (
            f"Observation(configs={self._configs}, score={self._scores}, "
            "contexts={self._contexts}, metadata={self._metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Observations):
            return False

        if not self._configs.equals(other._configs):
            return False
        if not self._scores.equals(other._scores):
            return False
        if not compare_optional_dataframe(self._contexts, other._contexts):
            return False
        if not compare_optional_dataframe(self._metadata, other._metadata):
            return False

        return True

    # required as per: https://stackoverflow.com/questions/30643236/does-ne-use-an-overridden-eq
    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


class Suggestion:
    """
    A single suggestion for a configuration.

    A Suggestion is an Observation that has not yet been scored. Evaluating the
    Suggestion and calling `complete(scores)` can convert it to an Observation.
    """

    def __init__(
        self,
        *,
        config: pd.Series,
        context: pd.Series | None = None,
        metadata: pd.Series | None = None,
    ):
        """
        Creates a new Suggestion.

        Parameters
        ----------
        config : pandas.Series
            The configuration suggested.
        context : pandas.Series | None
            The context for this suggestion, by default None
        metadata : pandas.Series | None
            Any metadata provided by the underlying optimizer, by default None
        """
        self._config = config
        self._context = context
        self._metadata = metadata

    @property
    def config(self) -> pd.Series:
        """Gets (a copy of) the config of the Suggestion."""
        return self._config.copy()

    @property
    def context(self) -> pd.Series | None:
        """Gets (a copy of) the context of the Suggestion."""
        return self._context.copy() if self._context is not None else None

    @property
    def metadata(self) -> pd.Series | None:
        """Gets (a copy of) the metadata of the Suggestion."""
        return self._metadata.copy() if self._metadata is not None else None

    def complete(self, score: pd.Series) -> Observation:
        """
        Completes the Suggestion by adding a score to turn it into an Observation.

        Parameters
        ----------
        score : pandas.Series
            The score metrics observed.

        Returns
        -------
        Observation
            The observation of the suggestion.
        """
        return Observation(
            config=self.config,
            score=score,
            context=self.context,
            metadata=self.metadata,
        )

    def to_configspace_config(self, space: ConfigurationSpace) -> Configuration:
        """
        Convert a Configuration Space to a Configuration.

        Parameters
        ----------
        space : ConfigSpace.ConfigurationSpace
            The ConfigurationSpace to be converted.

        Returns
        -------
        ConfigSpace.Configuration
            The output Configuration.
        """
        return Configuration(space, values=self._config.dropna().to_dict())

    def __repr__(self) -> str:
        return (
            f"Suggestion(config={self._config}, context={self._context}, "
            "metadata={self._metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Suggestion):
            return False

        if not self._config.equals(other._config):
            return False
        if not compare_optional_series(self._context, other._context):
            return False
        if not compare_optional_series(self._metadata, other._metadata):
            return False

        return True

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
