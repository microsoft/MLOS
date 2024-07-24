#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Contains classes for observations and suggestions."""

from __future__ import annotations

from typing import Any, Iterator, Optional

import pandas as pd


def compare_optional_dataframe(
    left: Optional[pd.DataFrame], right: Optional[pd.DataFrame]
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
    if left is None and right is not None:
        return False
    if left is not None and right is None:
        return False
    elif left is not None and right is not None:
        if not left.equals(right):
            return False
    return True


class Observation:
    """
    A set of observations of a configuration's score.

    Attributes
    ----------
    config : pd.DataFrame
        Pandas dataframe with a single row. Column names are the parameter names.
    score : Optional[pd.Series]
        The score metrics observed.
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
    ):
        assert len(config.index) == len(score.index), "config and score must have the same length"

        self.config = config
        self.score = score
        self.context = context
        self.metadata = metadata

    def filter_by_index(self, index: pd.Index) -> Observation:
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
        return Observation(
            config=self.config.loc[index],
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
        if len(self.config.index) == 0:
            self.config = other.config
            self.score = other.score
            self.context = other.context
            self.metadata = other.metadata
            return

        self.config = pd.concat([self.config, other.config]).reset_index(drop=True)
        self.score = pd.concat([self.score, other.score]).reset_index(drop=True)
        if self.context is not None:
            assert other.context is not None, (
                "context of appending observation must not be null"
                + " if context of prior observation is not null"
            )
            self.context = pd.concat([self.context, other.context]).reset_index(drop=True)
        else:
            assert other.context is None, (
                "context of appending observation must be null"
                + " if context of prior observation is null"
            )
        if self.metadata is not None:
            assert other.metadata is not None, (
                "context of appending observation must not be null"
                + " if metadata of prior observation is not null"
            )
            self.metadata = pd.concat([self.metadata, other.metadata]).reset_index(drop=True)
        else:
            assert other.metadata is None, (
                "context of appending observation must be null"
                + " if metadata of prior observation is null"
            )

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

    def __len__(self) -> int:
        return len(self.config.index)

    def __iter__(self) -> Iterator[Observation]:
        for idx in self.config.index:
            yield Observation(
                config=self.config.loc[[idx]],
                score=self.score.loc[[idx]],
                context=None if self.context is None else self.context.loc[[idx]],
                metadata=None if self.metadata is None else self.metadata.loc[[idx]],
            )

    def __repr__(self) -> str:
        return (
            f"Observation(config={self.config}, score={self.score},"
            + " context={self.context}, metadata={self.metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Observation):
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

    Attributes
    ----------
    config : pd.DataFrame
        The suggested configuration.
    """

    def __init__(
        self,
        *,
        config: pd.DataFrame,
        context: Optional[pd.DataFrame] = None,
        metadata: Optional[pd.DataFrame] = None,
    ):
        self.config = config
        self.context = context
        self.metadata = metadata

    def complete(self, score: pd.DataFrame) -> Observation:
        """
        Completes the suggestion.

        Parameters
        ----------
        score : pd.Series
            The score metrics observed.

        Returns
        -------
        Observation
            The observation of the suggestion.
        """
        assert len(score) == len(self.config), "score must have the same length as the config"

        return Observation(
            config=self.config,
            score=score,
            context=self.context,
            metadata=self.metadata,
        )

    def __repr__(self) -> str:
        return (
            f"Suggestion(config={self.config}, context={self.context}, metadata={self.metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Suggestion):
            return False

        if not self.config.equals(other.config):
            return False
        if not compare_optional_dataframe(self.context, other.context):
            return False
        if not compare_optional_dataframe(self.metadata, other.metadata):
            return False

        return True

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
