"""
Scheduler-side environment to mock the benchmark results.
"""

import random
import logging
from typing import Optional, Tuple

import numpy
import pandas

from mlos_bench.environment.status import Status
from mlos_bench.environment.base_environment import Environment
from mlos_bench.service.base_service import Service
from mlos_bench.tunables import Tunable, TunableGroups

_LOG = logging.getLogger(__name__)


class MockEnv(Environment):
    """
    Scheduler-side environment to mock the benchmark results.
    """

    _NOISE_VAR = 0.2  # Variance of the Gaussian noise added to the benchmark value.

    def __init__(self,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
        # pylint: disable=too-many-arguments
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
            The two optional arguments are `seed` and `range`.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object. Not used by this class.
        """
        super().__init__(name, config, global_config, tunables, service)
        seed = self.config.get("seed")
        self._random = random.Random(seed) if seed is not None else None
        self._range = self.config.get("range")
        self._is_ready = True

    def benchmark(self) -> Tuple[Status, pandas.DataFrame]:
        """
        Produce mock benchmark data for one experiment.

        Returns
        -------
        (benchmark_status, benchmark_result) : (Status, pandas.DataFrame)
            A pair of (benchmark status, benchmark result) values.
            benchmark_result is a one-row DataFrame containing final
            benchmark results or None if the status is not COMPLETED.
        """
        (status, _) = result = super().benchmark()
        if not status.is_ready:
            return result

        # Simple convex function of all tunable parameters.
        score = numpy.mean(numpy.square([
            self._normalized(tunable) for (tunable, _group) in self._tunable_params
        ]))

        # Add noise and shift the benchmark value from [0, 1] to a given range.
        noise = self._random.gauss(0, MockEnv._NOISE_VAR) if self._random else 0
        score = numpy.clip(score + noise, 0, 1)
        if self._range:
            score = self._range[0] + score * (self._range[1] - self._range[0])

        data = pandas.DataFrame({"score": [score]})
        return (Status.SUCCEEDED, data)

    @staticmethod
    def _normalized(tunable: Tunable) -> float:
        """
        Get the NORMALIZED value of a tunable.
        That is, map current value to the [0, 1] range.
        """
        val = None
        if tunable.type == "categorical":
            val = (tunable.categorical_values.index(tunable.value) /
                   float(len(tunable.categorical_values) - 1))
        elif tunable.type in {"int", "float"}:
            if not tunable.range:
                raise ValueError("Tunable must have a range: " + tunable.name)
            val = ((tunable.value - tunable.range[0]) /
                   float(tunable.range[1] - tunable.range[0]))
        else:
            raise ValueError("Invalid parameter type: " + tunable.type)
        # Explicitly clip the value in case of numerical errors.
        return numpy.clip(val, 0, 1)
