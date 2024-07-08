#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Scheduler-side environment to mock the benchmark results."""

import logging
import random
from datetime import datetime
from typing import Dict, Optional, Tuple

import numpy

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.tunables import Tunable, TunableGroups, TunableValue

_LOG = logging.getLogger(__name__)


class MockEnv(Environment):
    """Scheduler-side environment to mock the benchmark results."""

    _NOISE_VAR = 0.2
    """Variance of the Gaussian noise added to the benchmark value."""

    def __init__(
        self,
        *,
        name: str,
        config: dict,
        global_config: Optional[dict] = None,
        tunables: Optional[TunableGroups] = None,
        service: Optional[Service] = None,
    ):
        """
        Create a new environment that produces mock benchmark data.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment configuration.
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
            Optional arguments are `mock_env_seed`, `mock_env_range`, and `mock_env_metrics`.
            Set `mock_env_seed` to -1 for deterministic behavior, 0 for default randomness.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object. Not used by this class.
        """
        super().__init__(
            name=name,
            config=config,
            global_config=global_config,
            tunables=tunables,
            service=service,
        )
        seed = int(self.config.get("mock_env_seed", -1))
        self._random = random.Random(seed or None) if seed >= 0 else None
        self._range = self.config.get("mock_env_range")
        self._metrics = self.config.get("mock_env_metrics", ["score"])
        self._is_ready = True

    def run(self) -> Tuple[Status, datetime, Optional[Dict[str, TunableValue]]]:
        """
        Produce mock benchmark data for one experiment.

        Returns
        -------
        (status, timestamp, output) : (Status, datetime, dict)
            3-tuple of (Status, timestamp, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            The keys of the `output` dict are the names of the metrics
            specified in the config; by default it's just one metric
            named "score". All output metrics have the same value.
        """
        (status, timestamp, _) = result = super().run()
        if not status.is_ready():
            return result

        # Simple convex function of all tunable parameters.
        score = numpy.mean(
            numpy.square([self._normalized(tunable) for (tunable, _group) in self._tunable_params])
        )

        # Add noise and shift the benchmark value from [0, 1] to a given range.
        noise = self._random.gauss(0, self._NOISE_VAR) if self._random else 0
        score = numpy.clip(score + noise, 0, 1)
        if self._range:
            score = self._range[0] + score * (self._range[1] - self._range[0])

        return (Status.SUCCEEDED, timestamp, {metric: score for metric in self._metrics})

    @staticmethod
    def _normalized(tunable: Tunable) -> float:
        """
        Get the NORMALIZED value of a tunable.

        That is, map current value to the [0, 1] range.
        """
        val = None
        if tunable.is_categorical:
            val = tunable.categories.index(tunable.category) / float(len(tunable.categories) - 1)
        elif tunable.is_numerical:
            val = (tunable.numerical_value - tunable.range[0]) / float(
                tunable.range[1] - tunable.range[0]
            )
        else:
            raise ValueError("Invalid parameter type: " + tunable.type)
        # Explicitly clip the value in case of numerical errors.
        ret: float = numpy.clip(val, 0, 1)
        return ret
