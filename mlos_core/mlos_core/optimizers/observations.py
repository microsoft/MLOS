#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Contains classes for observations and suggestions."""

from __future__ import annotations

from typing import Any, Iterator, List, Optional

import pandas as pd
from ConfigSpace import Configuration, ConfigurationSpace


def compare_optional_series(left: Optional[pd.Series], right: Optional[pd.Series]) -> bool:
    """
    Compare Series that may also be None.

    Parameters
    ----------
    left : Optional[pd.Series]
        The left Series to compare
    right : Optional[pd.Series]
        The right Series to compare

    Returns
    -------
    bool
        Compare the equality of two Optional[pd.Series] objects
    """
    if type(left) != type(right):
        return False
    elif left is not None and right is not None:
        if not left.equals(right):
            return False
    return True


def compare_optional_dataframe(
    left: Optional[pd.DataFrame], right: Optional[pd.DataFrame],
) -> bool:
    """
    Compare DataFrames that may also be None.

    Parameters
    ----------
    left : Optional[pd.DataFrame]
        The left DataFrame to compare
    right : Optional[pd.DataFrame]
        The right DataFrame to compare

    Returns
    -------
    bool
        Compare the equality of two Optional[pd.DataFrame] objects
    """
    if type(left) != type(right):
        return False
    elif left is not None and right is not None:
        if not left.equals(right):
            return False
    return True


class Observation:
    """
    A single observation of a configuration.

    Attributes
    ----------
    config : pd.Series
        The configuration observed.
    score : pd.Series
        The score metrics observed.
    context : Optional[pd.Series]
        The context in which the configuration was evaluated.
        Not Yet Implemented.
    metadata: Optional[pd.Series]
        The metadata in which the configuration was evaluated
    """

    def __init__(
        self,
        *,
        config: pd.Series,
        score: pd.Series = pd.Series(),
        context: Optional[pd.Series] = None,
        metadata: Optional[pd.Series] = None,
    ):
        self.config = config
        self.score = score
        self.context = context
        self.metadata = metadata

    def to_suggestion(self) -> Suggestion:
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


class Observations:
    """
    A set of observations of a configuration's score.

    Attributes
    ----------
    config : pd.DataFrame
        Pandas dataframe containing configurations. Column names are the parameter names.
    score : pd.DataFrame
        The score metrics observed in a dataframe.
    context : Optional[pd.Series]
        The context in which the configuration was evaluated.
        Not Yet Implemented.
    metadata: Optional[pd.Series]
        The metadata in which the configuration was evaluated
        Not Yet Implemented.
    """

    def __init__(
        self,
        *,
        config: pd.DataFrame = pd.DataFrame(),
        score: pd.DataFrame = pd.DataFrame(),
        context: Optional[pd.DataFrame] = None,
        metadata: Optional[pd.DataFrame] = None,
        observations: List[Observation] = [],
    ):

        if len(observations) > 0:
            config = pd.concat([obs.config.to_frame().T for obs in observations])
            score = pd.concat([obs.score.to_frame().T for obs in observations])
            assert (len(config.index) == len(score.index)), "config and score must have same length"
                score.index
            ), "config and score must have the same length"

            if sum([obs.context is None for obs in observations]) == 0:
                context = pd.concat([obs.context.to_frame().T for obs in observations])  # type: ignore
            else:
                context = None
            if sum([obs.metadata is None for obs in observations]) == 0:
                metadata = pd.concat([obs.metadata.to_frame().T for obs in observations])  # type: ignore[specific-rule]
            else:
                metadata = None

        assert len(config.index) == len(score.index), "config and score must have the same length"
        self.config = config
        self.score = score
        self.context = context
        self.metadata = metadata

    def filter_by_index(self, index: pd.Index) -> Observations:
        """
        Filters the observation by the given indices.

        Parameters
        ----------
        index : pd.Index
            The indices to filter by.

        Returns
        -------
        Observation
            The filtered observation.
        """
        return Observations(
            config=self.config.loc[index].copy(),
            score=self.score.loc[index],
            context=None if self.context is None else self.context.loc[index],
            metadata=None if self.metadata is None else self.metadata.loc[index],
        )

    def append(self, other: Observation) -> None:
        """
        Appends the given observation to this observation.

        Parameters
        ----------
        other : Observation
            The observation to append.
        """
        config = other.config.to_frame().T
        score = other.score.to_frame().T
        context = None if other.context is None else other.context.to_frame().T
        metadata = None if other.metadata is None else other.metadata.to_frame().T
        if len(self.config.index) == 0:
            self.config = config
            self.score = score
            self.context = context
            self.metadata = metadata
            assert set(self.config.index) == set(
                self.score.index
            ), "config and score must have the same index"
            return

        self.config = pd.concat([self.config, config]).reset_index(drop=True)
        self.score = pd.concat([self.score, score]).reset_index(drop=True)
        assert set(self.config.index) == set(
            self.score.index
        ), "config and score must have the same index"

        if self.context is not None:
            assert context is not None, (
                "context of appending observation must not be null"
                + " if context of prior observation is not null"
            )
            self.context = pd.concat([self.context, context]).reset_index(drop=True)
            assert self.config.index.equals(
                self.context.index
            ), "config and context must have the same index"
        else:
            assert context is None, (
                "context of appending observation must be null"
                + " if context of prior observation is null"
            )
        if self.metadata is not None:
            assert metadata is not None, (
                "context of appending observation must not be null"
                + " if metadata of prior observation is not null"
            )
            self.metadata = pd.concat([self.metadata, metadata]).reset_index(drop=True)
            assert self.config.index.equals(
                self.metadata.index
            ), "config and metadata must have the same index"
        else:
            assert metadata is None, (
                "context of appending observation must be null"
                " if metadata of prior observation is null"
            )

    def to_list(self) -> List[Observation]:
        """
        Converts the Observations object to a list of Observation objects.

        Returns
        -------
        List[Observation]
            The list of observations.
        """
        return [
            Observation(
                config=self.config.loc[idx],
                score=self.score.loc[idx],
                context=None if self.context is None else self.context.loc[idx],
                metadata=None if self.metadata is None else self.metadata.loc[idx],
            )
            for idx in self.config.index
        ]

    def __len__(self) -> int:
        return len(self.config.index)

    def __iter__(self) -> Iterator[Observations]:
        for idx in self.config.index:
            yield Observations(
                config=self.config.loc[[idx]],
                score=self.score.loc[[idx]],
                context=None if self.context is None else self.context.loc[[idx]],
                metadata=None if self.metadata is None else self.metadata.loc[[idx]],
            )

    def __repr__(self) -> str:
        return (
            f"Observation(config={self.config}, score={self.score},"
            " context={self.context}, metadata={self.metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Observations):
            return False

        if not self.config.equals(other.config):
            return False
        if not self.score.equals(other.score):
            return False
        if not compare_optional_dataframe(self.context, other.context):
            return False
        if not compare_optional_dataframe(self.metadata, other.metadata):
            return False

        return True

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


class Suggestion:
    """
    A single suggestion for a configuration.
    
    A Suggestion is an Observation that has not yet been scored.
    Evaluating the Suggestion and calling `complete(scores)` can convert it to an Observation. 

    Attributes
    ----------
    config : pd.DataFrame
        The suggested configuration.
    """

    def __init__(
        self,
        *,
        config: pd.Series,
        context: Optional[pd.Series] = None,
        metadata: Optional[pd.Series] = None,
    ):
        self.config = config
        self.context = context
        self.metadata = metadata

    def complete(self, score: pd.Series) -> Observation:
        """
        Completes the Suggestion by adding a score to turn it into an Observation.

        Parameters
        ----------
        score : pd.Series
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
        return Configuration(space, values=self.config.to_dict())

    def __repr__(self) -> str:
        return (
            f"Suggestion(config={self.config}, context={self.context}, metadata={self.metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Suggestion):
            return False

        if not self.config.equals(other.config):
            return False
        if not compare_optional_series(self.context, other.context):
            return False
        if not compare_optional_series(self.metadata, other.metadata):
            return False

        return True

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
