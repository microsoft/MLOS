from typing import Any, Optional

import pandas as pd

from mlos_core.mlos_core.data_classes.suggestion import Suggestion
from mlos_core.mlos_core.util import compare_optional_series


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
        self._config = config
        self._score = score
        self._context = context
        self._metadata = metadata

    def to_suggestion(self) -> Suggestion:
        """
        Converts the observation to a suggestion.

        Returns
        -------
        Suggestion
            The suggestion.
        """
        return Suggestion(
            config=self._config,
            context=self._context,
            metadata=self._metadata,
        )

    def __repr__(self) -> str:
        return f"Observation(config={self._}, score={self._score}, context={self._context}, metadata={self._metadata})"

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
