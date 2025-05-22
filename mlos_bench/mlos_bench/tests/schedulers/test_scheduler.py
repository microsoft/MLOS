#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for :py:class:`mlos_bench.schedulers` and their internals.
"""

from unittest.mock import patch
import sys

import pytest

from mlos_core.tests import get_all_concrete_subclasses
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.schedulers.trial_runner import TrialRunner
import mlos_bench.tests.optimizers.fixtures as optimizers_fixtures

mock_opt = optimizers_fixtures.mock_opt

# pylint: disable=redefined-outer-name


def create_scheduler(
    scheduler_type: type[Scheduler],
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
) -> Scheduler:
    """Create a Scheduler instance using trial_runners, mock_opt, and
    sqlite_storage fixtures."""

    env = trial_runners[0].environment
    assert isinstance(env, MockEnv), "Environment is not a MockEnv instance."
    max_trials = max(trial_id for trial_id in env.mock_trial_data.keys())
    max_trials = min(max_trials, mock_opt.max_suggestions)

    return scheduler_type(
        config={
            "max_trials": max_trials,
        },
        global_config={
            "experiment_id": "Test{scheduler_type.__name__}Experiment",
            "trial_id": 1,
            # TODO: Adjust this in the future?
            "trial_repeat_count": 1,
        },
        trial_runners=trial_runners,
        optimizer=mock_opt,
        storage=sqlite_storage,
        root_env_config="",
    )


scheduler_classes = get_all_concrete_subclasses(
    Scheduler,  # type: ignore[type-abstract]
    pkg_name="mlos_bench",
)
assert scheduler_classes, "No Scheduler classes found in mlos_bench."


@pytest.mark.parametrize(
    "scheduler_class",
    scheduler_classes,
)
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Skipping test on Windows - SQLite storage is not accessible in parallel tests there.",
)
def test_scheduler(
    scheduler_class: type[Scheduler],
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
) -> None:
    """
    Full integration test for Scheduler: runs trials, checks storage, optimizer
    registration, and internal bookkeeping.
    """
    # pylint: disable=too-many-locals

    # Create the scheduler.
    scheduler = create_scheduler(
        scheduler_class,
        trial_runners,
        mock_opt,
        sqlite_storage,
    )

    root_env = scheduler.root_environment
    assert isinstance(root_env, MockEnv), "Root environment is not a MockEnv instance."
    mock_trial_data = root_env.mock_trial_data

    # Patch bulk_register and add_new_optimizer_suggestions
    with (
        patch.object(
            scheduler.optimizer,
            "bulk_register",
            wraps=scheduler.optimizer.bulk_register,
        ) as mock_bulk_register,
        patch.object(
            scheduler,
            "add_new_optimizer_suggestions",
            wraps=scheduler.add_new_optimizer_suggestions,
        ) as mock_add_suggestions,
    ):
        # Run the scheduler
        with scheduler:
            scheduler.start()
            scheduler.teardown()

        # Now check the results.
        # TODO

        # 1. Check results in storage
        experiments = scheduler.storage.experiments
        assert experiments, "No experiments found in storage."
        # Get the first experiment
        experiment = next(iter(experiments.values()))
        trials = experiment.trials
        # Compare with mock_trial_data from root_environment
        for trial_id, trial_data in trials.items():
            # Check that the trial result matches the mock data
            expected = mock_trial_data[trial_id].run.metrics
            actual = trial_data.results_dict
            assert actual == expected, f"Trial {trial_id} results {actual} != expected {expected}"

        # 1b. Check ran_trials bookkeeping
        ran_trials = scheduler.ran_trials
        assert len(ran_trials) == len(trials)
        for trial in ran_trials:
            assert (
                trial.status.is_ready()
            ), f"Trial {trial.trial_id} did not complete successfully."

        # 2. Check optimizer registration
        assert mock_bulk_register.called, "bulk_register was not called on optimizer."
        # Check that the configs and scores match the mock_trial_data
        for call in mock_bulk_register.call_args_list:
            configs, scores, *_ = call.args
            for i, config in enumerate(configs):
                trial_id = i  # assumes order matches
                expected_score = mock_trial_data[trial_id].run.metrics
                assert (
                    scores[i] == expected_score
                ), f"bulk_register score {scores[i]} != expected {expected_score} for trial {trial_id}"

        # 3. Check bookkeeping: add_new_optimizer_suggestions and _last_trial_id
        assert mock_add_suggestions.called, "add_new_optimizer_suggestions was not called."
        # _last_trial_id should be the last trial id
        assert getattr(scheduler, "_last_trial_id", None) == max(trials.keys())
