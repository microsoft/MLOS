#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import Any, Iterator, List, Optional, Tuple

import pandas as pd


def compare_optional_series(left: Optional[pd.Series], right: Optional[pd.Series]) -> bool:
    if left is None and right is not None:
        return False
    if left is not None and right is None:
        return False
    elif left is not None and right is not None:
        if not left.equals(right):
            return False
    return True


def compare_optional_dataframe(
    left: Optional[pd.DataFrame], right: Optional[pd.DataFrame]
) -> bool:
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
    A single observation of a configuration's performance.
    Attributes
    ----------
    config : pd.DataFrame
        Pandas dataframe with a single row. Column names are the parameter names.
    performance : Optional[pd.Series]
        The performance metrics observed.
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
        config: pd.DataFrame,
        performance: pd.DataFrame,
        context: Optional[pd.DataFrame] = None,
        metadata: Optional[pd.DataFrame] = None,
    ):
        self.config = config
        self.performance = performance
        self.context = context
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"Observation(config={self.config}, performance={self.performance}, context={self.context}, metadata={self.metadata})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Observation):
            return False

        if not self.config.equals(other.config):
            return False
        if not self.performance.equals(other.performance):
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

    def evaluate(self, performance: pd.DataFrame) -> Observation:
        """
        Completes the suggestion.
        Parameters
        ----------
        performance : pd.Series
            The performance metrics observed.
        Returns
        -------
        Observation
            The observation of the suggestion.
        """

        assert len(performance) == len(
            self.config
        ), "Performance must have the same length as the config"

        return Observation(
            config=self.config,
            performance=performance,
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


class Observations:
    """
    A collection of observations.
    Attributes
    ----------
    observations : List[Observation]
        The list of observations.
    """

    def __init__(self, observations: List[Observation] = []):
        self.observations = observations

    def append(self, observation: Observation) -> None:
        """
        Appends an observation to the collection.
        Parameters
        ----------
        Observation : observation
            The observation to append.
        """

        self.observations.append(observation)

    def __iter__(self) -> Iterator[Observation]:
        return iter(self.observations)

    def to_legacy(
        self,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Hack to allow for iteration over the observations.
        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]
            Legacy access pattern
        """

        configs: pd.DataFrame = pd.concat([o.config for o in self.observations]).reset_index(
            drop=True
        )
        scores: pd.DataFrame = pd.concat([o.performance for o in self.observations]).reset_index(
            drop=True
        )
        contexts: pd.DataFrame = pd.concat(
            [pd.DataFrame() if o.context is None else o.context for o in self.observations]
        ).reset_index(drop=True)
        metadata: pd.DataFrame = pd.concat(
            [pd.DataFrame() if o.metadata is None else o.metadata for o in self.observations]
        ).reset_index(drop=True)

        return (
            configs,
            scores,
            contexts if len(contexts.columns) > 0 else None,
            metadata if len(metadata.columns) > 0 else None,
        )

    def __repr__(self) -> str:
        return f"Observations(observations={self.observations})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Observations):
            return False
        if len(self.observations) != len(other.observations):
            return False
        for self_observation, other_observation in zip(self.observations, other.observations):
            if self_observation != other_observation:
                return False
        return True

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
