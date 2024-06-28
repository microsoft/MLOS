#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Toy optimization loop to test the optimizers on mock benchmark environment.
"""

from typing import Tuple

import logging

import pytest

from mlos_core.util import config_to_dataframe
from mlos_core.optimizers.bayesian_optimizers.smac_optimizer import SmacOptimizer
from mlos_bench.optimizers.convert_configspace import tunable_values_to_configuration

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer


# For debugging purposes output some warnings which are captured with failed tests.
DEBUG = True
logger = logging.debug
if DEBUG:
    logger = logging.warning


def _optimize(env: Environment, opt: Optimizer) -> Tuple[float, TunableGroups]:
    """
    Toy optimization loop.
    """
    assert opt.not_converged()

    while opt.not_converged():

        with env as env_context:

            tunables = opt.suggest()

            logger("tunables: %s", str(tunables))
            # pylint: disable=protected-access
            if isinstance(opt, MlosCoreOptimizer) and isinstance(opt._opt, SmacOptimizer):
                config = tunable_values_to_configuration(tunables)
                config_df = config_to_dataframe(config)
                logger("config: %s", str(config))
                try:
                    logger("prediction: %s", opt._opt.surrogate_predict(configs=config_df))
                except RuntimeError:
                    pass

            assert env_context.setup(tunables)

            (status, _ts, output) = env_context.run()
            assert status.is_succeeded()
            assert output is not None
            score = output['score']
            assert isinstance(score, float)
            assert 60 <= score <= 120
            logger("score: %s", str(score))

            opt.register(tunables, status, output)

    (best_score, best_tunables) = opt.get_best_observation()
    assert best_score is not None and len(best_score) == 1
    assert isinstance(best_tunables, TunableGroups)
    return (best_score["score"], best_tunables)


def test_mock_optimization_loop(mock_env_no_noise: MockEnv,
                                mock_opt: MockOptimizer) -> None:
    """
    Toy optimization loop with mock environment and optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, mock_opt)
    assert score == pytest.approx(64.9, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B2ms",
        "idle": "halt",
        "kernel_sched_migration_cost_ns": 117026,
        "kernel_sched_latency_ns": 149827706,
    }


def test_mock_optimization_loop_no_defaults(mock_env_no_noise: MockEnv,
                                            mock_opt_no_defaults: MockOptimizer) -> None:
    """
    Toy optimization loop with mock environment and optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, mock_opt_no_defaults)
    assert score == pytest.approx(60.97, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B2s",
        "idle": "halt",
        "kernel_sched_migration_cost_ns": 49123,
        "kernel_sched_latency_ns": 234760738,
    }


def test_flaml_optimization_loop(mock_env_no_noise: MockEnv,
                                 flaml_opt: MlosCoreOptimizer) -> None:
    """
    Toy optimization loop with mock environment and FLAML optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, flaml_opt)
    assert score == pytest.approx(60.15, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B2s",
        "idle": "halt",
        "kernel_sched_migration_cost_ns": -1,
        "kernel_sched_latency_ns": 13718105,
    }


# @pytest.mark.skip(reason="SMAC is not deterministic")
def test_smac_optimization_loop(mock_env_no_noise: MockEnv,
                                smac_opt: MlosCoreOptimizer) -> None:
    """
    Toy optimization loop with mock environment and SMAC optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, smac_opt)
    expected_score = 70.33
    expected_tunable_values = {
        "vmSize": "Standard_B2s",
        "idle": "mwait",
        "kernel_sched_migration_cost_ns": 297669,
        "kernel_sched_latency_ns": 290365137,
    }
    assert score == pytest.approx(expected_score, 0.01)
    assert tunables.get_param_values() == expected_tunable_values
