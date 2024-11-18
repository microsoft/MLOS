#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Contains classes for observations and suggestions."""
from __future__ import annotations

from typing import Any, Iterator, List, Optional

import pandas as pd

from mlos_core.mlos_core.data_classes.observation import Observation
from mlos_core.mlos_core.util import compare_optional_dataframe


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
            config = pd.concat([obs._config.to_frame().T for obs in observations])
            score = pd.concat([obs._score.to_frame().T for obs in observations])
            assert (
                len(config.index) == len(score.index),
                "config and score must have same length",
            )

            if sum([obs._context is None for obs in observations]) == 0:
                context = pd.concat([obs._context.to_frame().T for obs in observations])  # type: ignore
            else:
                context = None
            if sum([obs._metadata is None for obs in observations]) == 0:
                metadata = pd.concat([obs._metadata.to_frame().T for obs in observations])  # type: ignore[specific-rule]
            else:
                metadata = None

        assert len(config.index) == len(score.index), "config and score must have the same length"
        if context is not None:
            assert len(config.index) == len(
                context.index
            ), "config and context must have the same length"
        if metadata is not None:
            assert len(config.index) == len(
                metadata.index
            ), "config and metadata must have the same length"
        self._config = config
        self._score = score
        self._context = context
        self._metadata = metadata

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
            config=self._config.loc[index].copy(),
            score=self._score.loc[index],
            context=None if self._context is None else self._context.loc[index],
            metadata=None if self._metadata is None else self._metadata.loc[index],
        )

    def append(self, other: Observation) -> None:
        """
        Appends the given observation to this observation.

        Parameters
        ----------
        other : Observation
            The observation to append.
        """
        config = other._config.to_frame().T
        score = other._score.to_frame().T
        context = None if other._context is None else other._context.to_frame().T
        metadata = None if other._metadata is None else other._metadata.to_frame().T
        if len(self._config.index) == 0:
            self._config = config
            self._score = score
            self._context = context
            self._metadata = metadata
            assert set(self._config.index) == set(
                self._score.index
            ), "config and score must have the same index"
            return

        self._config = pd.concat([self._config, config]).reset_index(drop=True)
        self._score = pd.concat([self._score, score]).reset_index(drop=True)
        assert set(self._config.index) == set(
            self._score.index
        ), "config and score must have the same index"

        if self._context is not None:
            assert context is not None, (
                "context of appending observation must not be null"
                + " if context of prior observation is not null"
            )
            self._context = pd.concat([self._context, context]).reset_index(drop=True)
            assert self._config.index.equals(
                self._context.index
            ), "config and context must have the same index"
        else:
            assert context is None, (
                "context of appending observation must be null"
                + " if context of prior observation is null"
            )
        if self._metadata is not None:
            assert metadata is not None, (
                "context of appending observation must not be null"
                + " if metadata of prior observation is not null"
            )
            self._metadata = pd.concat([self._metadata, metadata]).reset_index(drop=True)
            assert self._config.index.equals(
                self._metadata.index
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
                config=self._config.loc[idx],
                score=self._score.loc[idx],
                context=None if self._context is None else self._context.loc[idx],
                metadata=None if self._metadata is None else self._metadata.loc[idx],
            )
            for idx in self._config.index
        ]

    def __len__(self) -> int:
        return len(self._config.index)

    def __iter__(self) -> Iterator[Observations]:
        for idx in self._config.index:
            yield Observations(
                config=self._config.loc[[idx]],
                score=self._score.loc[[idx]],
                context=None if self._context is None else self._context.loc[[idx]],
                metadata=None if self._metadata is None else self._metadata.loc[[idx]],
            )

    def __repr__(self) -> str:
        return (
            f"Observation(config={self._config}, score={self._score},"
            " context={self.context}, metadata={self.metadata})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Observations):
            return False

        if not self._config.equals(other._config):
            return False
        if not self._score.equals(other._score):
            return False
        if not compare_optional_dataframe(self._context, other._context):
            return False
        if not compare_optional_dataframe(self._metadata, other._metadata):
            return False

        return True

    # required as per: https://stackoverflow.com/questions/30643236/does-ne-use-an-overridden-eq
    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
