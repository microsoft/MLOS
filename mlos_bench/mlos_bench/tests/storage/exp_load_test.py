#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the storage subsystem.
"""

from mlos_bench.storage import Storage
from mlos_bench.tunables import TunableGroups

# pylint: disable=redefined-outer-name


def test_exp_load_empty(exp_storage_memory_sql: Storage.Experiment):
    """
    Try to retrieve old experimental data from the empty storage.
    """
    (configs, scores) = exp_storage_memory_sql.load('score')
    assert not configs
    assert not scores


def test_exp_pending_empty(exp_storage_memory_sql: Storage.Experiment):
    """
    Try to retrieve pending experiments from the empty storage.
    """
    trials = list(exp_storage_memory_sql.pending())
    assert not trials


def test_exp_trial_pending(exp_storage_memory_sql: Storage.Experiment,
                           tunable_groups: TunableGroups):
    """
    Start a trial and check that it is pending.
    """
    trial = exp_storage_memory_sql.trial(tunable_groups)
    (pending,) = list(exp_storage_memory_sql.pending())
    assert pending.trial_id == trial.trial_id
