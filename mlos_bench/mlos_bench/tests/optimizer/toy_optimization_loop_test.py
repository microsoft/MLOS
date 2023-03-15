"""
Toy optimization loop to test the optimizers on mock benchmark environment.
"""

from typing import Tuple

import pytest

from mlos_bench.environment import Environment, MockEnv
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizer import Optimizer, MockOptimizer, MlosCoreOptimizer


def _optimize(env: Environment, opt: Optimizer) -> Tuple[float, TunableGroups]:
    """
    Toy optimization loop.
    """
    assert opt.not_converged()

    while opt.not_converged():

        tunables = opt.suggest()
        assert env.setup(tunables)

        (status, value) = env.benchmark()
        assert status.is_succeeded
        score = value.loc[0, 'score']
        assert 60 <= score <= 120

        opt.register(tunables, status, score)

    return opt.get_best_observation()


def test_mock_optimization_loop(mock_env_no_noise: MockEnv,
                                mock_opt: MockOptimizer):
    """
    Toy optimization loop with mock environment and optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, mock_opt)
    assert score == pytest.approx(80.0, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "rootfs": "xfs",
        "kernel_sched_migration_cost_ns": 13111
    }


def test_scikit_gp_optimization_loop(mock_env_no_noise: MockEnv,
                                     scikit_gp_opt: MlosCoreOptimizer):
    """
    Toy optimization loop with mock environment and Scikit GP optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, scikit_gp_opt)
    assert score == pytest.approx(80.0, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "rootfs": "ext2",
        "kernel_sched_migration_cost_ns": 398271
    }


def test_scikit_et_optimization_loop(mock_env_no_noise: MockEnv,
                                     scikit_et_opt: MlosCoreOptimizer):
    """
    Toy optimization loop with mock environment and Scikit ET optimizer.
    """
    (score, tunables) = _optimize(mock_env_no_noise, scikit_et_opt)
    assert score == pytest.approx(80.0, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "rootfs": "ext2",
        "kernel_sched_migration_cost_ns": 146866
    }


def test_emukit_optimization_loop(mock_env_no_noise: MockEnv,
                                  emukit_opt: MlosCoreOptimizer):
    """
    Toy optimization loop with mock environment and EmuKit optimizer.
    """
    (score, _tunables) = _optimize(mock_env_no_noise, emukit_opt)
    assert score == pytest.approx(80.0, 0.01)
    # Emukit optimizer is not deterministic, so we can't assert the exact values of the tunables.


def test_emukit_optimization_loop_max(mock_env_no_noise: MockEnv,
                                      emukit_opt_max: MlosCoreOptimizer):
    """
    Toy optimization loop with mock environment and EmuKit optimizer
    in maximization mode.
    """
    (score, _tunables) = _optimize(mock_env_no_noise, emukit_opt_max)
    assert score == pytest.approx(80.0, 0.01)
    # Emukit optimizer is not deterministic, so we can't assert the exact values of the tunables.
