#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A wrapper for mlos_core optimizers for mlos_bench.
"""

import logging
import os

from types import TracebackType
from typing import Dict, Optional, Sequence, Tuple, Type, Union
from typing_extensions import Literal

import pandas as pd

from mlos_core.optimizers import (
    BaseOptimizer, OptimizerType, OptimizerFactory, SpaceAdapterType, DEFAULT_OPTIMIZER_TYPE
)

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.base_optimizer import Optimizer

from mlos_bench.optimizers.convert_configspace import (
    TunableValueKind,
    configspace_data_to_tunable_values,
    special_param_names,
    tunable_groups_to_configspace,
)

_LOG = logging.getLogger(__name__)


class MlosCoreOptimizer(Optimizer):
    """
    A wrapper class for the mlos_core optimizers.
    """

    def __init__(self,
                 tunables: TunableGroups,
                 config: dict,
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
        super().__init__(tunables, config, global_config, service)

        seed = config.get("seed")
        seed = None if seed is None else int(seed)

        space = tunable_groups_to_configspace(tunables, seed)
        _LOG.debug("ConfigSpace: %s", space)

        opt_type = getattr(OptimizerType, self._config.pop(
            'optimizer_type', DEFAULT_OPTIMIZER_TYPE.name))

        if opt_type == OptimizerType.SMAC:

            output_directory = self._config.get('output_directory')
            if output_directory is not None:
                # If output_directory is specified, turn it into an absolute path.
                self._config['output_directory'] = os.path.abspath(output_directory)
            else:
                _LOG.warning("SMAC optimizer output_directory was null. SMAC will use a temporary directory.")

            # Make sure max_trials >= max_iterations.
            if 'max_trials' not in self._config:
                self._config['max_trials'] = self._max_iter
            assert int(self._config['max_trials']) >= self._max_iter, \
                f"max_trials {self._config.get('max_trials')} <= max_iterations {self._max_iter}"

            if 'run_name' not in self._config and self.experiment_id:
                self._config['run_name'] = self.experiment_id

        space_adapter_type = self._config.pop('space_adapter_type', None)
        space_adapter_config = self._config.pop('space_adapter_config', {})

        if space_adapter_type is not None:
            space_adapter_type = getattr(SpaceAdapterType, space_adapter_type)

        self._opt: BaseOptimizer = OptimizerFactory.create(
            parameter_space=space,
            optimizer_type=opt_type,
            optimizer_kwargs=self._config,
            space_adapter_type=space_adapter_type,
            space_adapter_kwargs=space_adapter_config,
        )

    def __exit__(self, ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]) -> Literal[False]:
        self._opt.cleanup()
        return super().__exit__(ex_type, ex_val, ex_tb)

    @property
    def name(self) -> str:
        return f"{self.__class__.__name__}:{self._opt.__class__.__name__}"

    def bulk_register(self, configs: Sequence[dict], scores: Sequence[Optional[float]],
                      status: Optional[Sequence[Status]] = None) -> bool:
        if not super().bulk_register(configs, scores, status):
            return False
        df_configs = self._to_df(configs)  # Impute missing values, if necessary
        df_scores = pd.Series(scores, dtype=float) * self._opt_sign
        if status is not None:
            df_status = pd.Series(status)
            df_scores[df_status != Status.SUCCEEDED] = float("inf")
            df_status_completed = df_status.apply(Status.is_completed)
            df_configs = df_configs[df_status_completed]
            df_scores = df_scores[df_status_completed]
        self._opt.register(df_configs, df_scores)
        if _LOG.isEnabledFor(logging.DEBUG):
            (score, _) = self.get_best_observation()
            _LOG.debug("Warm-up end: %s = %s", self.target, score)
        return True

    def _to_df(self, configs: Sequence[Dict[str, TunableValue]]) -> pd.DataFrame:
        """
        Select from past trials only the columns required in this experiment and
        impute default values for the tunables that are missing in the dataframe.

        Parameters
        ----------
        configs : Sequence[dict]
            Sequence of dicts with past trials data.

        Returns
        -------
        df_configs : pd.DataFrame
            A dataframe with past trials data, with missing values imputed.
        """
        df_configs = pd.DataFrame(configs)
        tunables_names = list(self._tunables.get_param_values().keys())
        missing_cols = set(tunables_names).difference(df_configs.columns)
        for (tunable, _group) in self._tunables:
            if tunable.name in missing_cols:
                df_configs[tunable.name] = tunable.default
            else:
                df_configs[tunable.name].fillna(tunable.default, inplace=True)
            # External data can have incorrect types (e.g., all strings).
            df_configs[tunable.name] = df_configs[tunable.name].astype(tunable.dtype)
            # Add columns for tunables with special values.
            if tunable.special:
                (special_name, type_name) = special_param_names(tunable.name)
                tunables_names += [special_name, type_name]
                is_special = df_configs[tunable.name].apply(tunable.special.__contains__)
                df_configs[type_name] = TunableValueKind.RANGE
                df_configs.loc[is_special, type_name] = TunableValueKind.SPECIAL
                if tunable.type == "int":
                    # Make int column NULLABLE:
                    df_configs[tunable.name] = df_configs[tunable.name].astype("Int64")
                df_configs[special_name] = df_configs[tunable.name]
                df_configs.loc[~is_special, special_name] = None
                df_configs.loc[is_special, tunable.name] = None
        # By default, hyperparameters in ConfigurationSpace are sorted by name:
        df_configs = df_configs[sorted(tunables_names)]
        _LOG.debug("Loaded configs:\n%s", df_configs)
        return df_configs

    def suggest(self) -> TunableGroups:
        if self._start_with_defaults:
            _LOG.info("Use default values for the first trial")
        df_config = self._opt.suggest(defaults=self._start_with_defaults)
        self._start_with_defaults = False
        _LOG.info("Iteration %d :: Suggest:\n%s", self._iter, df_config)
        return self._tunables.copy().assign(
            configspace_data_to_tunable_values(df_config.loc[0].to_dict()))

    def register(self, tunables: TunableGroups, status: Status,
                 score: Optional[Union[float, dict]] = None) -> Optional[float]:
        score = super().register(tunables, status, score)  # With _opt_sign applied
        if status.is_completed():
            df_config = self._to_df([tunables.get_param_values()])
            _LOG.debug("Score: %s Dataframe:\n%s", score, df_config)
            self._opt.register(df_config, pd.Series([score], dtype=float))
        self._iter += 1
        return score

    def get_best_observation(self) -> Union[Tuple[float, TunableGroups], Tuple[None, None]]:
        df_config = self._opt.get_best_observation()
        if len(df_config) == 0:
            return (None, None)
        params = configspace_data_to_tunable_values(df_config.iloc[0].to_dict())
        _LOG.debug("Best observation: %s", params)
        score = params.pop("score") * self._opt_sign  # mlos_core always uses the `score` column
        return (score, self._tunables.copy().assign(params))
