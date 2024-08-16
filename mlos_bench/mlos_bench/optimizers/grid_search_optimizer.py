#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Grid search optimizer for mlos_bench."""

import logging
from typing import Dict, Iterable, Optional, Sequence, Set, Tuple

import ConfigSpace
import numpy as np
from ConfigSpace.util import generate_grid

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.convert_configspace import configspace_data_to_tunable_values
from mlos_bench.optimizers.track_best_optimizer import TrackBestOptimizer
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class GridSearchOptimizer(TrackBestOptimizer):
    """Grid search optimizer."""

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: Optional[dict] = None,
        service: Optional[Service] = None,
    ):
        super().__init__(tunables, config, global_config, service)

        # Track the grid as a set of tuples of tunable values and reconstruct the
        # dicts as necessary.
        # Note: this is not the most efficient way to do this, but avoids
        # introducing a new data structure for hashable dicts.
        # See https://github.com/microsoft/MLOS/pull/690 for further discussion.

        self._sanity_check()
        # The ordered set of pending configs that have not yet been suggested.
        self._config_keys, self._pending_configs = self._get_grid()
        assert self._pending_configs
        # A set of suggested configs that have not yet been registered.
        self._suggested_configs: Set[Tuple[TunableValue, ...]] = set()

    def _sanity_check(self) -> None:
        size = np.prod([tunable.cardinality for (tunable, _group) in self._tunables])
        if size == np.inf:
            raise ValueError(
                f"Unquantized tunables are not supported for grid search: {self._tunables}"
            )
        if size > 10000:
            _LOG.warning(
                "Large number %d of config points requested for grid search: %s",
                size,
                self._tunables,
            )
        if size > self._max_iter:
            _LOG.warning(
                "Grid search size %d, is greater than max iterations %d",
                size,
                self._max_iter,
            )

    def _get_grid(self) -> Tuple[Tuple[str, ...], Dict[Tuple[TunableValue, ...], None]]:
        """
        Gets a grid of configs to try.

        Order is given by ConfigSpace, but preserved by dict ordering semantics.
        """
        # Since we are using ConfigSpace to generate the grid, but only tracking the
        # values as (ordered) tuples, we also need to use its ordering on column
        # names instead of the order given by TunableGroups.
        configs = [
            configspace_data_to_tunable_values(dict(config))
            for config in generate_grid(
                self.config_space,
                {
                    tunable.name: int(tunable.cardinality)
                    for (tunable, _group) in self._tunables
                    if tunable.quantization or tunable.type == "int"
                },
            )
        ]
        names = set(tuple(configs.keys()) for configs in configs)
        assert len(names) == 1
        return names.pop(), {tuple(configs.values()): None for configs in configs}

    @property
    def pending_configs(self) -> Iterable[Dict[str, TunableValue]]:
        """
        Gets the set of pending configs in this grid search optimizer.

        Returns
        -------
        Iterable[Dict[str, TunableValue]]
        """
        # See NOTEs above.
        return (dict(zip(self._config_keys, config)) for config in self._pending_configs.keys())

    @property
    def suggested_configs(self) -> Iterable[Dict[str, TunableValue]]:
        """
        Gets the set of configs that have been suggested but not yet registered.

        Returns
        -------
        Iterable[Dict[str, TunableValue]]
        """
        # See NOTEs above.
        return (dict(zip(self._config_keys, config)) for config in self._suggested_configs)

    def bulk_register(
        self,
        configs: Sequence[dict],
        scores: Sequence[Optional[Dict[str, TunableValue]]],
        status: Optional[Sequence[Status]] = None,
    ) -> bool:
        if not super().bulk_register(configs, scores, status):
            return False
        if status is None:
            status = [Status.SUCCEEDED] * len(configs)
        for params, score, trial_status in zip(configs, scores, status):
            tunables = self._tunables.copy().assign(params)
            self.register(tunables, trial_status, score)
        if _LOG.isEnabledFor(logging.DEBUG):
            (best_score, _) = self.get_best_observation()
            _LOG.debug("Update END: %s = %s", self, best_score)
        return True

    def suggest(self) -> TunableGroups:
        """Generate the next grid search suggestion."""
        tunables = super().suggest()
        if self._start_with_defaults:
            _LOG.info("Use default values for the first trial")
            self._start_with_defaults = False
            tunables = tunables.restore_defaults()
            # Need to index based on ConfigSpace dict ordering.
            default_config = dict(self.config_space.get_default_configuration())
            assert tunables.get_param_values() == default_config
            # Move the default from the pending to the suggested set.
            default_config_values = tuple(default_config.values())
            del self._pending_configs[default_config_values]
            self._suggested_configs.add(default_config_values)
        else:
            # Select the first item from the pending configs.
            if not self._pending_configs and self._iter <= self._max_iter:
                _LOG.info("No more pending configs to suggest. Restarting grid.")
                self._config_keys, self._pending_configs = self._get_grid()
            try:
                next_config_values = next(iter(self._pending_configs.keys()))
            except StopIteration as exc:
                raise ValueError("No more pending configs to suggest.") from exc
            next_config = dict(zip(self._config_keys, next_config_values))
            tunables.assign(next_config)
            # Move it to the suggested set.
            self._suggested_configs.add(next_config_values)
            del self._pending_configs[next_config_values]
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables

    def register(
        self,
        tunables: TunableGroups,
        status: Status,
        score: Optional[Dict[str, TunableValue]] = None,
    ) -> Optional[Dict[str, float]]:
        registered_score = super().register(tunables, status, score)
        try:
            config = dict(
                ConfigSpace.Configuration(self.config_space, values=tunables.get_param_values())
            )
            self._suggested_configs.remove(tuple(config.values()))
        except KeyError:
            _LOG.warning(
                (
                    "Attempted to remove missing config "
                    "(previously registered?) from suggested set: %s"
                ),
                tunables,
            )
        return registered_score

    def not_converged(self) -> bool:
        if self._iter > self._max_iter:
            if bool(self._pending_configs):
                _LOG.warning(
                    "Exceeded max iterations, but still have %d pending configs: %s",
                    len(self._pending_configs),
                    list(self._pending_configs.keys()),
                )
            return False
        return bool(self._pending_configs)
