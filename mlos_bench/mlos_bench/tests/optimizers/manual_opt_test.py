#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for mock mlos_bench optimizer."""

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.manual_optimizer import ManualOptimizer

# pylint: disable=redefined-outer-name


def test_manual_optimizer(manual_opt: ManualOptimizer, mock_configs: list) -> None:
    """Make sure that manual optimizer produces consistent suggestions."""

    i = 0
    while manual_opt.not_converged():
        tunables = manual_opt.suggest()
        assert tunables.get_param_values() == mock_configs[i % len(mock_configs)]
        manual_opt.register(tunables, Status.SUCCEEDED, {"score": 123.0})
        i += 1
