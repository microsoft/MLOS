#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""RandomOptimizer class."""

from warnings import warn

import pandas as pd

from mlos_core.data_classes import Observations, Suggestion
from mlos_core.optimizers.optimizer import BaseOptimizer


class RandomOptimizer(BaseOptimizer):
    """
    Optimizer class that produces random suggestions.

    Useful for baseline comparison against Bayesian optimizers.
    """

    def _register(
        self,
        observations: Observations,
    ) -> None:
        """
        Registers the given config/score pairs.

        Notes
        -----
        Doesn't do anything on the RandomOptimizer except storing configs for logging.

        Parameters
        ----------
        observations : Observations
            The observations to register.
        """
        if observations.contexts is not None:
            warn(
                f"Not Implemented: Ignoring context {list(observations.contexts.index)}",
                UserWarning,
            )
        if observations.metadata is not None:
            warn(
                f"Not Implemented: Ignoring context {list(observations.metadata.index)}",
                UserWarning,
            )
        # should we pop them from self.pending_observations?

    def _suggest(
        self,
        *,
        context: pd.Series | None = None,
    ) -> Suggestion:
        """
        Suggests a new configuration.

        Sampled at random using ConfigSpace.

        Parameters
        ----------
        context : None
            Not Yet Implemented.

        Returns
        -------
        suggestion: Suggestion
            The suggestion to evaluate.
        """
        if context is not None:
            # not sure how that works here?
            warn(f"Not Implemented: Ignoring context {list(context.index)}", UserWarning)
        return Suggestion(
            config=pd.Series(self.optimizer_parameter_space.sample_configuration(), dtype=object),
            context=context,
            metadata=None,
        )

    def register_pending(self, pending: Suggestion) -> None:
        raise NotImplementedError()
        # self._pending_observations.append((configs, context))
