#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for internal methods of the `MlosCoreOptimizer`.
"""

from typing import List

import pandas
import pytest

from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer
from mlos_bench.tunables.tunable_groups import TunableGroups

from mlos_bench.tests import SEED

# pylint: disable=redefined-outer-name, protected-access


@pytest.fixture
def mlos_core_optimizer(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    An instance of a mlos_core optimizer (FLAML-based).
    """
    test_opt_config = {
        'optimizer_type': 'FLAML',
        'max_suggestions': 10,
        'seed': SEED,
        'optimization_targets': {
            'latency': 'min',
            'throughput': 'max',
        },
    }
    return MlosCoreOptimizer(tunable_groups, test_opt_config)


def test_df(mlos_core_optimizer: MlosCoreOptimizer, mock_configs: List[dict]) -> None:
    """
    Test `MlosCoreOptimizer._to_df()` method on tunables that have special values.
    """
    df_config = mlos_core_optimizer._to_df(mock_configs)
    assert isinstance(df_config, pandas.DataFrame)
    assert df_config.shape == (4, 6)
    assert set(df_config.columns) == {
        'kernel_sched_latency_ns',
        'kernel_sched_migration_cost_ns',
        'kernel_sched_migration_cost_ns!type',
        'kernel_sched_migration_cost_ns!special',
        'idle',
        'vmSize',
    }
    assert df_config.to_dict(orient='records') == [
        {
            'idle': 'halt',
            'kernel_sched_latency_ns': 1000000,
            'kernel_sched_migration_cost_ns': 50000,
            'kernel_sched_migration_cost_ns!special': None,
            'kernel_sched_migration_cost_ns!type': 'range',
            'vmSize': 'Standard_B4ms',
        },
        {
            'idle': 'halt',
            'kernel_sched_latency_ns': 2000000,
            'kernel_sched_migration_cost_ns': 40000,
            'kernel_sched_migration_cost_ns!special': None,
            'kernel_sched_migration_cost_ns!type': 'range',
            'vmSize': 'Standard_B4ms',
        },
        {
            'idle': 'mwait',
            'kernel_sched_latency_ns': 3000000,
            'kernel_sched_migration_cost_ns': None,  # The value is special!
            'kernel_sched_migration_cost_ns!special': -1,
            'kernel_sched_migration_cost_ns!type': 'special',
            'vmSize': 'Standard_B4ms',
        },
        {
            'idle': 'mwait',
            'kernel_sched_latency_ns': 4000000,
            'kernel_sched_migration_cost_ns': 200000,
            'kernel_sched_migration_cost_ns!special': None,
            'kernel_sched_migration_cost_ns!type': 'range',
            'vmSize': 'Standard_B2s',
        },
    ]


def test_df_str(mlos_core_optimizer: MlosCoreOptimizer, mock_configs: List[dict]) -> None:
    """
    Test `MlosCoreOptimizer._to_df()` type coercion on tunables with string values.
    """
    df_config_orig = mlos_core_optimizer._to_df(mock_configs)
    df_config_str = mlos_core_optimizer._to_df([
        {key: str(val) for (key, val) in config.items()}
        for config in mock_configs
    ])
    assert df_config_orig.equals(df_config_str)


def test_adjust_signs_df(mlos_core_optimizer: MlosCoreOptimizer) -> None:
    """
    Test `MlosCoreOptimizer._adjust_signs_df()` on different types of inputs.
    """
    df_scores_input = pandas.DataFrame({
        'latency': [88.88, 66.66, 99.99, None],
        'throughput': [111, 222, 333, None],
    })

    df_scores_output = pandas.DataFrame({
        'latency': [88.88, 66.66, 99.99, float("NaN")],
        'throughput': [-111, -222, -333, float("NaN")],
    })

    # Make sure we adjust the signs for minimization.
    df_scores = mlos_core_optimizer._adjust_signs_df(df_scores_input)
    assert df_scores.equals(df_scores_output)

    # Check that the same operation works for string inputs.
    df_scores = mlos_core_optimizer._adjust_signs_df(df_scores_input.astype(str))
    assert df_scores.equals(df_scores_output)
