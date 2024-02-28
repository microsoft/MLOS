#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Mock optimizer for mlos_bench.
"""

import logging

from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from ConfigSpace.util import generate_grid

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.convert_configspace import configspace_data_to_tunable_values
from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


class HashableDict(dict):
    """
    Simple hashable dict implementation.
    """

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.items())))


class GridSearchOptimizer(Optimizer):
    """
    Grid search optimizer.
    """

    def __init__(self,
                 tunables: TunableGroups,
                 config: dict,
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
        super().__init__(tunables, config, global_config, service)

        self._sanity_check()
        self._configs = self._get_grid()
        assert self._configs
        self._suggested_config: HashableDict = HashableDict({})
        self._best_config: Optional[TunableGroups] = None
        self._best_score: Optional[float] = None

    def _sanity_check(self) -> None:
        size = 1
        for (tunable, _group) in self._tunables:
            cardinality = tunable.cardinality
            if cardinality == np.inf:
                raise ValueError(f"Unquantized tunables are not supported for grid search: {self.tunable_params}")
            size *= cardinality
        if cardinality > 10000:
            _LOG.warning("Large number of config points requested for grid search: %s", self.tunable_params)

    def _get_grid(self) -> Dict[HashableDict, None]:
        """
        Gets a grid of configs to try.
        Order is given by ConfigSpace, but preserved by dict ordering semantics.
        """
        return {
            HashableDict(configspace_data_to_tunable_values(config.get_dictionary())): None
            for config in
            generate_grid(self.config_space, {
                tunable.name: tunable.cardinality
                for (tunable, _group) in self._tunables
                if tunable.quantization or tunable.type == "int"
            })
        }

    @property
    def configs(self) -> List[dict]:
        """
        The remaining set of configs in this grid search optimizer.

        Returns
        -------
        List[dict]
        """
        return list(self._configs.keys())

    def bulk_register(self, configs: Sequence[dict], scores: Sequence[Optional[float]],
                      status: Optional[Sequence[Status]] = None, is_warm_up: bool = False) -> bool:
        if not super().bulk_register(configs, scores, status, is_warm_up):
            return False
        if status is None:
            status = [Status.SUCCEEDED] * len(configs)
        for (params, score, trial_status) in zip(configs, scores, status):
            tunables = self._tunables.copy().assign(params)
            self.register(tunables, trial_status, None if score is None else float(score))
            if is_warm_up:
                # Do not advance the iteration counter during warm-up.
                self._iter -= 1
        if _LOG.isEnabledFor(logging.DEBUG):
            (score, _) = self.get_best_observation()
            _LOG.debug("Warm-up end: %s = %s", self.target, score)
        return True

    def _advance_suggested_config(self) -> dict:
        """
        Advance to the next available config in the grid.

        Note: bulk registration may have removed some configs from the grid in an
        async order, we cannot maintain a single iterator, hence the somewhat
        ineffecient scanning.

        Returns
        -------
        dict
            The next config suggestion, or an empty dict if no more are available.
        """
        empty_config = HashableDict({})
        if not self._suggested_config:
            # None currently selected, pick the first available one.
            self._suggested_config = next(iter(self._configs, empty_config))
            return self._suggested_config
        # else, find the currently selected config.
        configs_iter = iter(self._configs)
        while config := next(configs_iter, empty_config):
            if config == self._suggested_config:
                # Pick the one after the one we were on.
                self._suggested_config = next(configs_iter, empty_config)
                break
        if not self._suggested_config:
            # We reached the end.  Try and start over from the begining, if there is one.
            self._suggested_config = next(iter(self._configs, empty_config))
        return self._suggested_config

    def _remove_config(self, config_to_remove: dict) -> None:
        """
        Remove a config from the grid and reset the suggested config pointer.
        """
        # Fallback in case there's no config before it.
        # This way we start from the first config again.
        predecessor = HashableDict({})
        for config in self._configs:
            # Find the config to remove and the one before it.
            if config == config_to_remove:
                del self._configs[config]
                self._suggested_config = predecessor
                break
            predecessor = config

    def suggest(self) -> TunableGroups:
        """
        Generate the next grid search suggestion.
        """
        tunables = self._tunables.copy()
        if self._start_with_defaults:
            _LOG.info("Use default values for the first trial")
            self._start_with_defaults = False
            tunables = tunables.restore_defaults()
            self._suggested_config = HashableDict(tunables.get_param_values())
        else:
            tunables.assign(self._advance_suggested_config())
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables

    def register(self, tunables: TunableGroups, status: Status,
                 score: Optional[Union[float, dict]] = None) -> Optional[float]:
        registered_score = super().register(tunables, status, score)
        if status.is_succeeded() and (
            self._best_score is None or (registered_score is not None and registered_score < self._best_score)
        ):
            self._best_score = registered_score
            self._best_config = tunables.copy()
        self._iter += 1
        self._remove_config(tunables.get_param_values())
        return registered_score

    def get_best_observation(self) -> Union[Tuple[float, TunableGroups], Tuple[None, None]]:
        if self._best_score is None:
            return (None, None)
        assert self._best_config is not None
        return (self._best_score * self._opt_sign, self._best_config)
