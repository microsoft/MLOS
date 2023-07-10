#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Toy optimization loop to test the optimizers on mock benchmark environment.
"""

from typing import Tuple

import pytest

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer


def _optimize(env: Environment, opt: Optimizer) -> Tuple[float, TunableGroups]:
    """
    Toy optimization loop.
    """
    assert opt.not_converged()

    while opt.not_converged():

        tunables = opt.suggest()
        assert env.setup(tunables)

        (status, output) = env.run()
        assert status.is_succeeded()
        assert output is not None
        score = output['score']
        assert 60 <= score <= 120

        opt.register(tunables, status, score)

    (best_score, best_tunables) = opt.get_best_observation()
    assert isinstance(best_score, float) and isinstance(best_tunables, TunableGroups)
    return (best_score, best_tunables)


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
        "kernel_sched_migration_cost_ns": 117025,
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
        "kernel_sched_migration_cost_ns": 49122,
        "kernel_sched_latency_ns": 234760738,
    }


def test_flaml_optimization_loop(mock_env_no_noise: MockEnv,
                                 flaml_opt: MlosCoreOptimizer) -> None:
    """
    Toy optimization loop with mock environment and FLAML optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, flaml_opt)
    assert score == pytest.approx(75.0, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "idle": "halt",
        "kernel_sched_migration_cost_ns": -1,
        "kernel_sched_latency_ns": 2000000,
    }


def test_smac_optimization_loop(mock_env_no_noise: MockEnv,
                                smac_opt: MlosCoreOptimizer) -> None:
    """
    Toy optimization loop with mock environment and SMAC optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, smac_opt)
    assert score == pytest.approx(75.0, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "idle": "halt",
        "kernel_sched_migration_cost_ns": -1,
        "kernel_sched_latency_ns": 2000000,
    }
