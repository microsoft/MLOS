"""
A wrapper for mlos_core optimizers for OS Autotune.
"""

import logging
from typing import Tuple

import pandas as pd

from mlos_core.optimizers import OptimizerType, OptimizerFactory

from mlos_bench.environment.status import Status
from mlos_bench.environment.tunable import TunableGroups

from mlos_bench.optimizer.base_optimizer import Optimizer
from mlos_bench.optimizer.convert_configspace import tunable_groups_to_configspace

_LOG = logging.getLogger(__name__)


class MlosCoreOptimizer(Optimizer):
    """
    A wrapper class for the mlos_core optimizers.
    """

    def __init__(self, tunables: TunableGroups, config: dict):
        super().__init__(tunables, config)
        space = tunable_groups_to_configspace(tunables)
        _LOG.debug("ConfigSpace: %s", space)
        opt_type = getattr(OptimizerType, self._config.pop('optimizer_type', 'SKOPT'))
        self._opt = OptimizerFactory.create(space, opt_type, optimizer_kwargs=self._config)

    def suggest(self) -> TunableGroups:
        df_config = self._opt.suggest()
        _LOG.info("Iteration %d :: Suggest:\n%s", self._iter, df_config)
        return self._tunables.copy().assign(df_config.loc[0].to_dict())

    def register(self, tunables: TunableGroups, status: Status, score: float):
        _LOG.info("Iteration %d :: Register: %s = %s score: %s",
                  self._iter, tunables, status, score)
        # By default, hyperparameters in ConfigurationSpace are sorted by name:
        df_config = pd.DataFrame(dict(sorted(tunables.get_param_values().items())), index=[0])
        _LOG.debug("Dataframe:\n%s", df_config)
        self._opt.register(df_config, pd.Series([score]))
        self._iter += 1

    def get_best_observation(self) -> Tuple[float, TunableGroups]:
        df_config = self._opt.get_best_observation()
        params = df_config.loc[0].to_dict()
        score = params.pop('score')
        return (score, self._tunables.copy().assign(params))
