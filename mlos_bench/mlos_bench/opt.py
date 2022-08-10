"""
Mock optimizer for OS Autotune.
"""

import logging

_LOG = logging.getLogger(__name__)


class Optimizer:
    """
    Mock optimizer to test the Environment API.
    """

    _MAX_ITER = 1

    def __init__(self, tunables):
        _LOG.info("Create: %s", tunables)
        self._iter_left = Optimizer._MAX_ITER
        self._tunables = tunables
        self._last_values = None

    def suggest(self):
        "Generate the next suggestion."
        # For now, get just the default values.
        # FIXME: Need to iterate over the actual values.
        tunables = {
            key: val.get("default") for (key, val) in self._tunables.items()
        }
        # TODO: Populate the tunables with some random values
        _LOG.info("Suggest: %s", tunables)
        return tunables

    def register(self, tunables, bench):
        "Register the observation for the given configuration."
        (bench_status, bench_result) = bench
        _LOG.info("Register: %s = %s %s", tunables, bench_status, bench_result)
        self._last_values = tunables
        self._iter_left -= 1

    def not_converged(self):
        "Return True if not converged, False otherwise."
        return self._iter_left > 0

    def get_best_observation(self):
        "Get the best observation so far."
        # FIXME: Use the tunables' values, as passed into .register()
        return (self._last_values, 0.0)
