#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Scheduler-side environment to mock the benchmark results.
"""

import random
import logging
from typing import Optional

import numpy

from mlos_bench.services.base_service import Service
from mlos_bench.environments.status import Status
from mlos_bench.environments.base_environment import Environment
from mlos_bench.tunables import Tunable, TunableGroups

_LOG = logging.getLogger(__name__)


class MockEnv(Environment):
    """
    Scheduler-side environment to mock the benchmark results.
    """

    _NOISE_VAR = 0.2
    """Variance of the Gaussian noise added to the benchmark value."""

    def __init__(self,
                 *,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
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
            Optional arguments are `seed`, `range`, and `metrics`.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object. Not used by this class.
        """
        super().__init__(name=name, config=config, global_config=global_config,
                         tunables=tunables, service=service)
        seed = self.config.get("seed")
        self._random = random.Random(seed) if seed is not None else None
        self._range = self.config.get("range")
        self._metrics = self.config.get("metrics", ["score"])
        self._update(Status.READY)  # Skip .setup()

    def run(self) -> bool:
        """
        Submit a new experiment to the environment.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        if not super().run():
            return False

        # Simple convex function of all tunable parameters.
        score = numpy.mean(numpy.square([
            self._normalized(tunable) for (tunable, _group) in self._tunable_params
        ]))

        # Add noise and shift the benchmark value from [0, 1] to a given range.
        noise = self._random.gauss(0, self._NOISE_VAR) if self._random else 0
        score = numpy.clip(score + noise, 0, 1)
        if self._range:
            score = self._range[0] + score * (self._range[1] - self._range[0])

        self._update(Status.SUCCEEDED)
        self._results = {metric: score for metric in self._metrics}
        return True

    @staticmethod
    def _normalized(tunable: Tunable) -> float:
        """
        Get the NORMALIZED value of a tunable.
        That is, map current value to the [0, 1] range.
        """
        val = None
        if tunable.is_categorical:
            val = (tunable.categories.index(tunable.category) /
                   float(len(tunable.categories) - 1))
        elif tunable.is_numerical:
            val = ((tunable.numerical_value - tunable.range[0]) /
                   float(tunable.range[1] - tunable.range[0]))
        else:
            raise ValueError("Invalid parameter type: " + tunable.type)
        # Explicitly clip the value in case of numerical errors.
        ret: float = numpy.clip(val, 0, 1)
        return ret
