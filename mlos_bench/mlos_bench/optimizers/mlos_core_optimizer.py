#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A wrapper for :py:mod:`mlos_core.optimizers` for :py:mod:`mlos_bench`.

Config
------
:py:mod:`mlos_bench.optimizers` has an overview of the configuration options for
the py:mod:`.MlosCoreOptimizer`.

See Also
--------
:py:mod:`mlos_bench.optimizers` :
    Another working example of an :py:class:`.MlosCoreOptimizer`.
:py:mod:`mlos_core.optimizers` :
    Documentation on the underlying mlos_core Optimizers.
:py:mod:`mlos_core.spaces.adapters` :
    Documentation on the underlying mlos_core SpaceAdapters.

Examples
--------
Load tunables from a JSON string.
Note: normally these would be automatically loaded from the
:py:mod:`~mlos_bench.environments.base_environment.Environment`'s
``include_tunables`` config parameter.

>>> import json5 as json
>>> import mlos_core.optimizers
>>> from mlos_bench.environments.status import Status
>>> from mlos_bench.services.config_persistence import ConfigPersistenceService
>>> service = ConfigPersistenceService()
>>> json_config = '''
... {
...   "group_1": {
...     "cost": 1,
...     "params": {
...       "flags": {
...         "type": "categorical",
...         "values": ["on", "off", "auto"],
...         "default": "auto",
...       },
...       "int_param": {
...         "type": "int",
...         "range": [1, 100],
...         "default": 10,
...       },
...       "float_param": {
...         "type": "float",
...         "range": [0, 100],
...         "default": 50.0,
...       }
...     }
...   }
... }
... '''
>>> tunables = service.load_tunables(jsons=[json_config])
>>> # Here's the defaults:
>>> tunables.get_param_values()
{'flags': 'auto', 'int_param': 10, 'float_param': 50.0}

When using the :py:class:`.MlosCoreOptimizer`, we can also specify some
additional properties, for instance the ``optimizer_type``, which is one of the
mlos_core :py:data:`~mlos_core.optimizers.OptimizerType` enum values:

>>> import mlos_core.optimizers
>>> print([member.name for member in mlos_core.optimizers.OptimizerType])
['RANDOM', 'FLAML', 'SMAC']

These may also include their own configuration options, which can be specified
as additional key-value pairs in the ``config`` section, where each key-value
corresponds to an argument to the respective OptimizerTypes's constructor.
See :py:meth:`mlos_core.optimizers.OptimizerFactory.create` for more details.

Other Optimizers may also have their own configuration options.
See each class' documentation for details.

When using :py:class:`.MlosCoreOptimizer`, we can also specify an optional an
``space_adapter_type``, which can sometimes help manipulate the configuration
space to something more manageable.  It should be one of the following
:py:data:`~mlos_core.spaces.adapters.SpaceAdapterType` enum values:

>>> import mlos_core.spaces.adapters
>>> print([member.name for member in mlos_core.spaces.adapters.SpaceAdapterType])
['IDENTITY', 'LLAMATUNE']

These may also include their own configuration options, which can be specified
as additional key-value pairs in the optional ``space_adapter_config`` section,
where each key-value corresponds to an argument to the respective
OptimizerTypes's constructor.  See
:py:meth:`mlos_core.spaces.adapters.SpaceAdapterFactory.create` for more details.

Here's an example JSON config for an :py:class:`.MlosCoreOptimizer`.

>>> optimizer_json_config = '''
... {
...   "class": "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer",
...   "description": "MlosCoreOptimizer",
...     "config": {
...         "max_suggestions": 1000,
...         "optimization_targets": {
...             "throughput": "max",
...             "cost": "min",
...         },
...         "start_with_defaults": true,
...         "seed": 42,
...         // Override the default optimizer type
...         // Must be one of the mlos_core OptimizerType enum values.
...         "optimizer_type": "SMAC",
...         // Optionally provide some additional configuration options for the optimizer.
...         // Note: these are optimizer-specific and may not be supported by all optimizers.
...         "n_random_init": 25,
...         "n_random_probability": 0.01,
...         // Optionally override the default space adapter type
...         // Must be one of the mlos_core SpaceAdapterType enum values.
...         // LlamaTune is a method for automatically doing space reduction
...         // from the original space.
...         "space_adapter_type": "LLAMATUNE",
...         "space_adapter_config": {
...             // Note: these values are probably too low,
...             // but it's just for demonstration.
...             "num_low_dims": 2,
...             "max_unique_values_per_param": 10,
...          }
...     }
... }
... '''

That config will typically be loaded via the ``--optimizer`` command-line
argument to the :py:mod:`mlos_bench <mlos_bench.run>` CLI.
However, for demonstration purposes, we can load it directly here:

>>> config = json.loads(optimizer_json_config)
>>> optimizer = service.build_optimizer(
...   tunables=tunables,
...   service=service,
...   config=config,
... )

Internally the Scheduler will call the Optimizer's methods to suggest
configurations, like so:

>>> suggested_config_1 = optimizer.suggest()
>>> # Normally default values should be suggested first, per json config.
>>> # However, since LlamaTune is being employed here, the first suggestion may
>>> # be projected to a slightly different space.
>>> suggested_config_1.get_param_values()
{'flags': 'auto', 'int_param': 1, 'float_param': 55.5555555555556}
>>> # Get another suggestion.
>>> # Note that multiple suggestions can be pending prior to
>>> # registering their scores, supporting parallel trial execution.
>>> suggested_config_2 = optimizer.suggest()
>>> suggested_config_2.get_param_values()
{'flags': 'on', 'int_param': 78, 'float_param': 88.8888888888889}
>>> # Register some scores.
>>> # Note: Maximization problems track negative scores to produce a minimization problem.
>>> optimizer.register(suggested_config_1, Status.SUCCEEDED, {"throughput": 42, "cost": 19})
{'throughput': -42.0, 'cost': 19.0}
>>> optimizer.register(suggested_config_2, Status.SUCCEEDED, {"throughput": 7, "cost": 17.2})
{'throughput': -7.0, 'cost': 17.2}
>>> (best_score, best_config) = optimizer.get_best_observation()
>>> best_score
{'throughput': 42.0, 'cost': 19.0}
>>> assert best_config == suggested_config_1
"""

import logging
import os
from collections.abc import Sequence
from types import TracebackType
from typing import Literal

import pandas as pd

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.convert_configspace import (
    TunableValueKind,
    configspace_data_to_tunable_values,
    special_param_names,
)
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tunables.tunable_types import TunableValue
from mlos_core.data_classes import Observations
from mlos_core.optimizers import (
    DEFAULT_OPTIMIZER_TYPE,
    BaseOptimizer,
    OptimizerFactory,
    OptimizerType,
    SpaceAdapterType,
)

_LOG = logging.getLogger(__name__)


class MlosCoreOptimizer(Optimizer):
    """A wrapper class for the :py:mod:`mlos_core.optimizers`."""

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        super().__init__(tunables, config, global_config, service)

        opt_type = getattr(
            OptimizerType, self._config.pop("optimizer_type", DEFAULT_OPTIMIZER_TYPE.name)
        )

        if opt_type == OptimizerType.SMAC:
            output_directory = self._config.get("output_directory")
            if output_directory is not None:
                # If output_directory is specified, turn it into an absolute path.
                self._config["output_directory"] = os.path.abspath(output_directory)
            else:
                _LOG.warning(
                    "SMAC optimizer output_directory was null. "
                    "SMAC will use a temporary directory."
                )

            # Make sure max_trials >= max_suggestions.
            if "max_trials" not in self._config:
                self._config["max_trials"] = self._max_suggestions
            assert int(self._config["max_trials"]) >= self._max_suggestions, (
                f"""max_trials {self._config.get("max_trials")} """
                f"<= max_suggestions{self._max_suggestions}"
            )

            if "run_name" not in self._config and self.experiment_id:
                self._config["run_name"] = self.experiment_id

        space_adapter_type = self._config.pop("space_adapter_type", None)
        space_adapter_config = self._config.pop("space_adapter_config", {})

        if space_adapter_type is not None:
            space_adapter_type = getattr(SpaceAdapterType, space_adapter_type)
            assert isinstance(space_adapter_type, SpaceAdapterType)
            if space_adapter_type == SpaceAdapterType.LLAMATUNE:
                # This is probably a sane default, especially when
                # bulk_registering old configs (e.g., Experiment resume), but is
                # not currently exposed in the config schema.
                space_adapter_config["use_approximate_reverse_mapping"] = True

        self._opt: BaseOptimizer = OptimizerFactory.create(
            parameter_space=self.config_space,
            optimization_targets=list(self._opt_targets),
            optimizer_type=opt_type,
            optimizer_kwargs=self._config,
            space_adapter_type=space_adapter_type,
            space_adapter_kwargs=space_adapter_config,
        )

    def __exit__(
        self,
        ex_type: type[BaseException] | None,
        ex_val: BaseException | None,
        ex_tb: TracebackType | None,
    ) -> Literal[False]:
        self._opt.cleanup()
        return super().__exit__(ex_type, ex_val, ex_tb)

    @property
    def name(self) -> str:
        return f"{self.__class__.__name__}:{self._opt.__class__.__name__}"

    def bulk_register(
        self,
        configs: Sequence[dict],
        scores: Sequence[dict[str, TunableValue] | None],
        status: Sequence[Status] | None = None,
    ) -> bool:

        if not super().bulk_register(configs, scores, status):
            return False

        df_configs = self._to_df(configs)  # Impute missing values, if necessary

        df_scores = self._adjust_signs_df(
            pd.DataFrame(
                [{} if score is None else score for score in scores],
                columns=list(self._opt_targets),
            )
        )

        if status is not None:
            # Select only the completed trials, set scores for failed trials to +inf.
            df_status = pd.Series(status)
            # TODO: Be more flexible with values used for failed trials (not just +inf).
            # Issue: https://github.com/microsoft/MLOS/issues/523
            df_scores[df_status != Status.SUCCEEDED] = float("inf")
            df_status_completed = df_status.apply(Status.is_completed)
            df_configs = df_configs[df_status_completed]
            df_scores = df_scores[df_status_completed]

        # TODO: Specify (in the config) which metrics to pass to the optimizer.
        # Issue: https://github.com/microsoft/MLOS/issues/745
        self._opt.register(observations=Observations(configs=df_configs, scores=df_scores))

        if _LOG.isEnabledFor(logging.DEBUG):
            (score, _) = self.get_best_observation()
            _LOG.debug("Warm-up END: %s :: %s", self, score)

        return True

    def _adjust_signs_df(self, df_scores: pd.DataFrame) -> pd.DataFrame:
        """Coerce optimization target scores to floats and adjust the signs for
        MINIMIZATION problem.
        """
        df_targets = df_scores[list(self._opt_targets)]
        try:
            return df_targets.astype(float) * self._opt_targets.values()
        except ValueError as ex:
            _LOG.error(
                "Some score values cannot be converted to float - check the data ::\n%s",
                df_targets,
                exc_info=True,
            )
            raise ValueError("Some score values cannot be converted to float") from ex

    def _to_df(self, configs: Sequence[dict[str, TunableValue]]) -> pd.DataFrame:
        """
        Select from past trials only the columns required in this experiment and impute
        default values for the tunables that are missing in the dataframe.

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
        for tunable, _group in self._tunables:
            if tunable.name in missing_cols:
                df_configs[tunable.name] = tunable.default
            else:
                df_configs.fillna({tunable.name: tunable.default}, inplace=True)
            # External data can have incorrect types (e.g., all strings).
            df_configs[tunable.name] = df_configs[tunable.name].astype(tunable.dtype)
            # Add columns for tunables with special values.
            if tunable.special:
                (special_name, type_name) = special_param_names(tunable.name)
                tunables_names += [special_name, type_name]
                is_special = df_configs[tunable.name].apply(tunable.special.__contains__)
                df_configs[type_name] = TunableValueKind.RANGE.value
                df_configs.loc[is_special, type_name] = TunableValueKind.SPECIAL.value
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
        tunables = super().suggest()
        if self._start_with_defaults:
            _LOG.info("Use default values for the first trial")
        suggestion = self._opt.suggest(defaults=self._start_with_defaults)
        self._start_with_defaults = False
        _LOG.info("Iteration %d :: Suggest:\n%s", self._iter, suggestion.config)
        return tunables.assign(configspace_data_to_tunable_values(suggestion.config.to_dict()))

    def register(
        self,
        tunables: TunableGroups,
        status: Status,
        score: dict[str, TunableValue] | None = None,
    ) -> dict[str, float] | None:
        registered_score = super().register(
            tunables,
            status,
            score,
        )  # Sign-adjusted for MINIMIZATION
        if status.is_completed():
            assert registered_score is not None
            df_config = self._to_df([tunables.get_param_values()])
            _LOG.debug("Score: %s Dataframe:\n%s", registered_score, df_config)
            # TODO: Specify (in the config) which metrics to pass to the optimizer.
            # Issue: https://github.com/microsoft/MLOS/issues/745
            self._opt.register(
                observations=Observations(
                    configs=df_config,
                    scores=pd.DataFrame([registered_score], dtype=float),
                )
            )
        return registered_score

    def get_best_observation(
        self,
    ) -> tuple[dict[str, float], TunableGroups] | tuple[None, None]:
        best_observations = self._opt.get_best_observations()
        if len(best_observations) == 0:
            return (None, None)
        params = configspace_data_to_tunable_values(best_observations.configs.iloc[0].to_dict())
        scores = self._adjust_signs_df(best_observations.scores).iloc[0].to_dict()
        _LOG.debug("Best observation: %s score: %s", params, scores)
        return (scores, self._tunables.copy().assign(params))
