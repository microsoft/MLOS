"""
Mock optimizer for OS Autotune.
"""

import random
import logging

_LOG = logging.getLogger(__name__)


class MockOptimizer:
    """
    Mock optimizer to test the Environment API.
    """

    _MAX_ITER = 3

    def __init__(self, tunables):
        _LOG.info("Create: %s", tunables)
        self._iter = 1
        self._tunables = tunables
        self._last_values = None

    def suggest(self):
        """
        Generate the next (random) suggestion.
        """
        tunables = self._tunables.copy()
        for (tunable, _group) in tunables:
            if tunable.type == "categorical":
                tunable.value = random.choice(tunable.categorical_values)
            elif tunable.type == "float":
                tunable.value = random.uniform(*tunable.range)
            elif tunable.type == "int":
                tunable.value = random.randint(*tunable.range)
            else:
                raise ValueError("Invalid parameter type: " + tunable.type)
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables

    def register(self, tunables, bench):
        """
        Register the observation for the given configuration.
        """
        (bench_status, bench_result) = bench
        _LOG.info("Iteration %d :: Register: %s = %s %s",
                  self._iter, tunables, bench_status, bench_result)
        self._last_values = tunables
        self._iter += 1

    def not_converged(self):
        """
        Return True if not converged, False otherwise.
        """
        return self._iter <= MockOptimizer._MAX_ITER

    def get_best_observation(self):
        """
        Get the best observation so far.
        """
        # FIXME: Use the tunables' values, as passed into .register()
        return (self._last_values, 0.0)
