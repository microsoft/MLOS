#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for :py:class:`mlos_bench.schedulers` and their internals."""

import sys

import pytest

import mlos_bench.tests.optimizers.fixtures as optimizers_fixtures
import mlos_bench.tests.storage.sql.fixtures as sql_storage_fixtures
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_core.tests import get_all_concrete_subclasses

mock_opt = optimizers_fixtures.mock_opt
sqlite_storage = sql_storage_fixtures.sqlite_storage

# pylint: disable=redefined-outer-name


def create_scheduler(
    scheduler_type: type[Scheduler],
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
    global_config: dict,
) -> Scheduler:
    """Create a Scheduler instance using trial_runners, mock_opt, and sqlite_storage
    fixtures.
    """
    env = trial_runners[0].environment
    assert isinstance(env, MockEnv), "Environment is not a MockEnv instance."
    max_trials = max(trial_id for trial_id in env.mock_trial_data.keys())
    max_trials = min(max_trials, mock_opt.max_suggestions)

    return scheduler_type(
        config={
            "max_trials": max_trials,
        },
        global_config=global_config,
        trial_runners=trial_runners,
        optimizer=mock_opt,
        storage=sqlite_storage,
        root_env_config="",
    )


def mock_opt_has_registered_trial_score(
    mock_opt: MockOptimizer,
    trial_data: TrialData,
) -> bool:
    """Check that the MockOptimizer has registered a given MockTrialData."""
    return any(
        registered_score.status == trial_data.status
        and registered_score.score == trial_data.results_dict
        and registered_score.config.get_param_values() == trial_data.tunable_config.config_dict
        for registered_score in mock_opt.registered_scores
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
def test_scheduler_with_mock_trial_data(
    scheduler_class: type[Scheduler],
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
    global_config: dict,
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
        global_config,
    )

    root_env = scheduler.root_environment
    experiment_id = root_env.experiment_id
    assert isinstance(root_env, MockEnv), f"Root environment {root_env} is not a MockEnv."
    assert root_env.mock_trial_data, "No mock trial data found in root environment."

    # Run the scheduler
    with scheduler:
        scheduler.start()
        scheduler.teardown()

    # Now check the overall results.
    ran_trials = {trial.trial_id for trial in scheduler.ran_trials}
    assert (
        experiment_id in sqlite_storage.experiments
    ), f"Experiment {experiment_id} not found in storage."
    exp_data = sqlite_storage.experiments[experiment_id]

    for mock_trial_data in root_env.mock_trial_data.values():
        trial_id = mock_trial_data.trial_id

        # Check the bookkeeping for ran_trials.
        assert trial_id in ran_trials, f"Trial {trial_id} not found in Scheduler.ran_trials."

        # Check the results in storage.
        assert trial_id in exp_data.trials, f"Trial {trial_id} not found in storage."
        trial_data = exp_data.trials[trial_id]

        # Check the results.
        metrics = mock_trial_data.run.metrics
        if metrics:
            for result_key, result_value in metrics.items():
                assert (
                    result_key in trial_data.results_dict
                ), f"Result {result_key} not found in storage for trial {trial_data}."
                assert (
                    trial_data.results_dict[result_key] == result_value
                ), f"Result value for {result_key} does not match expected value."
            # TODO: Should we check the reverse - no extra metrics were registered?
        # else: metrics weren't explicit in the mock trial data, so we only
        # check that a score was stored for the optimization target, but that's
        # good to do regardless
        for opt_target in mock_opt.targets:
            assert (
                opt_target in trial_data.results_dict
            ), f"Result column {opt_target} not found in storage."
            assert (
                trial_data.results_dict[opt_target] is not None
            ), f"Result value for {opt_target} is None."

        # Check that the appropriate sleeps occurred.
        trial_time_lb = 0.0
        trial_time_lb += mock_trial_data.setup.sleep or 0
        trial_time_lb += mock_trial_data.run.sleep or 0
        trial_time_lb += mock_trial_data.status.sleep or 0
        trial_time_lb += mock_trial_data.teardown.sleep or 0
        assert trial_data.ts_end is not None, f"Trial {trial_id} has no end time."
        trial_duration = trial_data.ts_end - trial_data.ts_start
        trial_dur_secs = trial_duration.total_seconds()
        assert (
            trial_dur_secs >= trial_time_lb
        ), f"Trial {trial_id} took less time ({trial_dur_secs}) than expected ({trial_time_lb}). "

        # Check that the trial status matches what we expected.
        assert (
            trial_data.status == mock_trial_data.run.status
        ), f"Trial {trial_id} status {trial_data.status} was not {mock_trial_data.run.status}."

        # TODO: Check the trial status telemetry.

        # Check the optimizer registration.
        assert mock_opt_has_registered_trial_score(
            mock_opt,
            trial_data,
        ), f"Trial {trial_id} was not registered in the optimizer."

    # TODO: And check the intermediary results.
    # 4. Check the bookkeeping for add_new_optimizer_suggestions and _last_trial_id.
    #    This last part may require patching and intercepting during the start()
    #    loop to validate in-progress book keeping instead of just overall.
