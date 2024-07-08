#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for internal methods of the `MlosCoreOptimizer`."""

from typing import List

import pandas
import pytest

from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer
from mlos_bench.tests import SEED
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name, protected-access


@pytest.fixture
def mlos_core_optimizer(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """An instance of a mlos_core optimizer (FLAML-based)."""
    test_opt_config = {
        "optimizer_type": "FLAML",
        "max_suggestions": 10,
        "seed": SEED,
    }
    return MlosCoreOptimizer(tunable_groups, test_opt_config)


def test_df(mlos_core_optimizer: MlosCoreOptimizer, mock_configs: List[dict]) -> None:
    """Test `MlosCoreOptimizer._to_df()` method on tunables that have special values."""
    df_config = mlos_core_optimizer._to_df(mock_configs)
    assert isinstance(df_config, pandas.DataFrame)
    assert df_config.shape == (4, 6)
    assert set(df_config.columns) == {
        "kernel_sched_latency_ns",
        "kernel_sched_migration_cost_ns",
        "kernel_sched_migration_cost_ns!type",
        "kernel_sched_migration_cost_ns!special",
        "idle",
        "vmSize",
    }
    assert df_config.to_dict(orient="records") == [
        {
            "idle": "halt",
            "kernel_sched_latency_ns": 1000000,
            "kernel_sched_migration_cost_ns": 50000,
            "kernel_sched_migration_cost_ns!special": None,
            "kernel_sched_migration_cost_ns!type": "range",
            "vmSize": "Standard_B4ms",
        },
        {
            "idle": "halt",
            "kernel_sched_latency_ns": 2000000,
            "kernel_sched_migration_cost_ns": 40000,
            "kernel_sched_migration_cost_ns!special": None,
            "kernel_sched_migration_cost_ns!type": "range",
            "vmSize": "Standard_B4ms",
        },
        {
            "idle": "mwait",
            "kernel_sched_latency_ns": 3000000,
            "kernel_sched_migration_cost_ns": None,  # The value is special!
            "kernel_sched_migration_cost_ns!special": -1,
            "kernel_sched_migration_cost_ns!type": "special",
            "vmSize": "Standard_B4ms",
        },
        {
            "idle": "mwait",
            "kernel_sched_latency_ns": 4000000,
            "kernel_sched_migration_cost_ns": 200000,
            "kernel_sched_migration_cost_ns!special": None,
            "kernel_sched_migration_cost_ns!type": "range",
            "vmSize": "Standard_B2s",
        },
    ]
