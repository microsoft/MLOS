#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Mock optimizer for mlos_bench.
"""

import logging

from typing import Dict, Iterable, Set, Optional, Sequence, Tuple, Union

import numpy as np
from ConfigSpace.util import generate_grid

from mlos_bench.environments.status import Status
from mlos_bench.tunables.hashable_tunable_values_dict import HashableTunableValuesDict
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.convert_configspace import configspace_data_to_tunable_values
from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


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
        self._pending_configs = self._get_grid()
        assert self._pending_configs
        self._suggested_configs: Set[HashableTunableValuesDict] = set()
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

    def _get_grid(self) -> Dict[HashableTunableValuesDict, None]:
        """
        Gets a grid of configs to try.
        Order is given by ConfigSpace, but preserved by dict ordering semantics.
        """
        return {
            configspace_data_to_tunable_values(config.get_dictionary()): None
            for config in
            generate_grid(self.config_space, {
                tunable.name: tunable.cardinality
                for (tunable, _group) in self._tunables
                if tunable.quantization or tunable.type == "int"
            })
        }

    @property
    def pending_configs(self) -> Iterable[HashableTunableValuesDict]:
        """
        Gets the set of pending configs in this grid search optimizer.

        Returns
        -------
        List[HashableTunableValuesDict]
        """
        return self._pending_configs.keys()

    @property
    def suggested_configs(self) -> Set[HashableTunableValuesDict]:
        """
        Gets the set of configs that have been suggested but not yet registered.

        Returns
        -------
        Set[HashableTunableValuesDict]
        """
        return self._suggested_configs

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

    def suggest(self) -> TunableGroups:
        """
        Generate the next grid search suggestion.
        """
        tunables = self._tunables.copy()
        if self._start_with_defaults:
            _LOG.info("Use default values for the first trial")
            self._start_with_defaults = False
            tunables = tunables.restore_defaults()
            default_config = tunables.get_param_values()
            # Move the default from the pending to the suggested set.
            del self._pending_configs[default_config]
            self._suggested_configs.add(default_config)
        else:
            # Select the first item from the pending configs.
            next_config = next(iter(self._pending_configs.keys()))
            tunables.assign(next_config)
            # Move it to the suggested set.
            self._suggested_configs.add(next_config)
            del self._pending_configs[next_config]
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
        try:
            self._suggested_configs.remove(tunables.get_param_values())
        except KeyError:
            pass
        return registered_score

    def get_best_observation(self) -> Union[Tuple[float, TunableGroups], Tuple[None, None]]:
        if self._best_score is None:
            return (None, None)
        assert self._best_config is not None
        return (self._best_score * self._opt_sign, self._best_config)
