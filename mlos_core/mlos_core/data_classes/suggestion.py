from typing import Any, Optional

import pandas as pd

from mlos_core.mlos_core.data_classes.observation import Observation
from ConfigSpace import Configuration, ConfigurationSpace
from mlos_core.mlos_core.util import compare_optional_series


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
        self._config = config
        self._context = context
        self._metadata = metadata

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
            config=self._config,
            score=score,
            context=self._context,
            metadata=self._metadata,
        )

    def to_configspace_config(self, space: ConfigurationSpace) -> Configuration:
        return Configuration(space, values=self.config.to_dict())

    def __repr__(self) -> str:
        return f"Suggestion(config={self._}, context={self._context}, metadata={self._metadata})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Suggestion):
            return False

        if not self.config.equals(other._config):
            return False
        if not compare_optional_series(self._context, other._context):
            return False
        if not compare_optional_series(self._metadata, other._metadata):
            return False

        return True

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
