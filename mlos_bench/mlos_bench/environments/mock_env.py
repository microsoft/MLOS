#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Scheduler-side environment to mock the benchmark results."""

import logging
import random
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tunables.tunable_types import TunableValue

_LOG = logging.getLogger(__name__)


@dataclass
class MockTrialPhaseData:
    """Mock trial data for a specific phase of a trial."""

    phase: str
    """Phase of the trial data (e.g., setup, run, status, teardown)."""

    status: Status
    """Status response for the phase."""

    metrics: dict[str, TunableValue] | None = None
    """Metrics response for the phase."""

    sleep: float | None = 0.0
    """Optional sleep time in seconds to simulate phase execution time."""

    exception: str | None = None
    """Message of an exception to raise for the phase."""

    @staticmethod
    def from_dict(phase: str, data: dict | None) -> "MockTrialPhaseData":
        """
        Create a MockTrialPhaseData instance from a dictionary.

        Parameters
        ----------
        phase : str
            Phase of the trial data.
        data : dict | None
            Dictionary containing the phase data.

        Returns
        -------
        MockTrialPhaseData
            Instance of MockTrialPhaseData.
        """
        data = data or {}
        assert phase in {"setup", "run", "status", "teardown"}, f"Invalid phase: {phase}"
        if phase in {"teardown", "status"}:
            # setup/teardown phase is not expected to have metrics or status.
            assert "metrics" not in data, f"Unexpected metrics data in {phase} phase: {data}"
            assert "status" not in data, f"Unexpected status data in {phase} phase: {data}"
        if "sleep" in data:
            assert isinstance(
                data["sleep"], (int, float)
            ), f"Invalid sleep in {phase} phase: {data}"
            assert 60 >= data["sleep"] >= 0, f"Invalid sleep time in {phase} phase: {data}"
        if "metrics" in data:
            assert isinstance(data["metrics"], dict), f"Invalid metrics in {phase} phase: {data}"
        default_phases = {
            "run": Status.SUCCEEDED,
            # FIXME: this causes issues if we report RUNNING instead of READY
            "status": Status.READY,
        }
        status = Status.parse(data.get("status", default_phases.get(phase, Status.UNKNOWN)))
        return MockTrialPhaseData(
            phase=phase,
            status=status,
            metrics=data.get("metrics"),
            sleep=data.get("sleep"),
            exception=data.get("exception"),
        )


@dataclass
class MockTrialData:
    """Mock trial data for a specific trial ID."""

    trial_id: int
    """Trial ID for the mock trial data."""
    setup: MockTrialPhaseData
    """Setup phase data for the trial."""
    run: MockTrialPhaseData
    """Run phase data for the trial."""
    status: MockTrialPhaseData
    """Status phase data for the trial."""
    teardown: MockTrialPhaseData
    """Teardown phase data for the trial."""

    @staticmethod
    def from_dict(trial_id: int, data: dict) -> "MockTrialData":
        """
        Create a MockTrialData instance from a dictionary.

        Parameters
        ----------
        trial_id : int
            Trial ID for the mock trial data.
        data : dict
            Dictionary containing the trial data.

        Returns
        -------
        MockTrialData
            Instance of MockTrialData.
        """
        return MockTrialData(
            trial_id=trial_id,
            setup=MockTrialPhaseData.from_dict("setup", data.get("setup")),
            run=MockTrialPhaseData.from_dict("run", data.get("run")),
            status=MockTrialPhaseData.from_dict("status", data.get("status")),
            teardown=MockTrialPhaseData.from_dict("teardown", data.get("teardown")),
        )

    @staticmethod
    def load_mock_trial_data(mock_trial_data: dict) -> dict[int, "MockTrialData"]:
        """
        Load mock trial data from a dictionary.

        Parameters
        ----------
        mock_trial_data : dict
            Dictionary containing mock trial data.

        Returns
        -------
        dict[int, MockTrialData]
            Dictionary of mock trial data keyed by trial ID.
        """
        return {
            int(trial_id): MockTrialData.from_dict(trial_id=int(trial_id), data=trial_data)
            for trial_id, trial_data in mock_trial_data.items()
        }


class MockEnv(Environment):
    """Scheduler-side environment to mock the benchmark results."""

    _NOISE_VAR = 0.2
    """Variance of the Gaussian noise added to the benchmark value."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        name: str,
        config: dict,
        global_config: dict | None = None,
        tunables: TunableGroups | None = None,
        service: Service | None = None,
    ):
        """
        Create a new environment that produces mock benchmark data.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment configuration.
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
            Optional arguments are `mock_env_seed`, `mock_env_range`, and `mock_env_metrics`.
            Set `mock_env_seed` to -1 for deterministic behavior, 0 for default randomness.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object. Not used by this class.
        """
        # First allow merging mock_trial_data from the global_config into the
        # config so we can check it against the JSON schema for expected data
        # types.
        if global_config and "mock_trial_data" in global_config:
            mock_trial_data = global_config["mock_trial_data"]
            if not isinstance(mock_trial_data, dict):
                raise ValueError(f"Invalid mock_trial_data in global_config: {mock_trial_data}")
            # Merge the mock trial data into the config.
            config["mock_trial_data"] = {
                **config.get("mock_trial_data", {}),
                **mock_trial_data,
            }

        super().__init__(
            name=name,
            config=config,
            global_config=global_config,
            tunables=tunables,
            service=service,
        )
        self._mock_trial_data = MockTrialData.load_mock_trial_data(
            self.config.get("mock_trial_data", {})
        )
        seed = int(self.config.get("mock_env_seed", -1))
        self._run_random = random.Random(seed or None) if seed >= 0 else None
        self._status_random = random.Random(seed or None) if seed >= 0 else None
        self._range: tuple[int, int] | None = self.config.get("mock_env_range")
        self._metrics: list[str] | None = self.config.get("mock_env_metrics", ["score"])
        self._is_ready = True

    def _produce_metrics(self, rand: random.Random | None) -> dict[str, TunableValue]:
        # Simple convex function of all tunable parameters.
        score = numpy.mean(
            numpy.square([self._normalized(tunable) for (tunable, _group) in self._tunable_params])
        )

        # Add noise and shift the benchmark value from [0, 1] to a given range.
        noise = rand.gauss(0, self._NOISE_VAR) if rand else 0
        score = numpy.clip(score + noise, 0, 1)
        if self._range:
            score = self._range[0] + score * (self._range[1] - self._range[0])

        return {metric: float(score) for metric in self._metrics or []}

    @property
    def mock_trial_data(self) -> dict[int, MockTrialData]:
        """
        Get the mock trial data for all trials.

        Returns
        -------
        dict[int, MockTrialData]
            Dictionary of mock trial data keyed by trial ID.
        """
        return deepcopy(self._mock_trial_data)

    def get_current_mock_trial_data(self) -> MockTrialData:
        """
        Gets mock trial data for the current trial ID.

        If no (or missing) mock trial data is found, a new instance of
        MockTrialData is created and later filled with random data.

        Note
        ----
        This method must be called after the base :py:meth:`.Environment.setup`
        method is called to ensure the current ``trial_id`` is set.
        """
        trial_id = self.current_trial_id
        mock_trial_data = self._mock_trial_data.get(trial_id)
        if not mock_trial_data:
            mock_trial_data = MockTrialData(
                trial_id=trial_id,
                setup=MockTrialPhaseData.from_dict(phase="setup", data=None),
                run=MockTrialPhaseData.from_dict(phase="run", data=None),
                status=MockTrialPhaseData.from_dict(phase="status", data=None),
                teardown=MockTrialPhaseData.from_dict(phase="teardown", data=None),
            )
            # Save the generated data for later.
            self._mock_trial_data[trial_id] = mock_trial_data
        return mock_trial_data

    def setup(self, tunables: TunableGroups, global_config: dict | None = None) -> bool:
        is_success = super().setup(tunables, global_config)
        mock_trial_data = self.get_current_mock_trial_data()
        if mock_trial_data.setup.sleep:
            _LOG.debug("Sleeping for %s seconds", mock_trial_data.setup.sleep)
            time.sleep(mock_trial_data.setup.sleep)
        if mock_trial_data.setup.exception:
            raise RuntimeError(
                f"Mock trial data setup exception: {mock_trial_data.setup.exception}"
            )
        return is_success

    def teardown(self) -> None:
        mock_trial_data = self.get_current_mock_trial_data()
        if mock_trial_data.teardown.sleep:
            _LOG.debug("Sleeping for %s seconds", mock_trial_data.teardown.sleep)
            time.sleep(mock_trial_data.teardown.sleep)
        if mock_trial_data.teardown.exception:
            raise RuntimeError(
                f"Mock trial data teardown exception: {mock_trial_data.teardown.exception}"
            )
        super().teardown()

    def run(self) -> tuple[Status, datetime, dict[str, TunableValue] | None]:
        """
        Produce mock benchmark data for one experiment.

        Returns
        -------
        (status, timestamp, output) : (Status, datetime.datetime, dict)
            3-tuple of (Status, timestamp, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            The keys of the `output` dict are the names of the metrics
            specified in the config; by default it's just one metric
            named "score". All output metrics have the same value.
        """
        (status, timestamp, _) = result = super().run()
        if not status.is_ready():
            return result
        mock_trial_data = self.get_current_mock_trial_data()
        if mock_trial_data.run.sleep:
            _LOG.debug("Sleeping for %s seconds", mock_trial_data.run.sleep)
            time.sleep(mock_trial_data.run.sleep)
        if mock_trial_data.run.exception:
            raise RuntimeError(f"Mock trial data run exception: {mock_trial_data.run.exception}")
        if mock_trial_data.run.metrics is None:
            # If no metrics are provided, generate them.
            mock_trial_data.run.metrics = self._produce_metrics(self._run_random)
        return (mock_trial_data.run.status, timestamp, mock_trial_data.run.metrics)

    def status(self) -> tuple[Status, datetime, list[tuple[datetime, str, Any]]]:
        """
        Produce mock benchmark status telemetry for one experiment.

        Returns
        -------
        (benchmark_status, timestamp, telemetry) : (Status, datetime.datetime, list)
            3-tuple of (benchmark status, timestamp, telemetry) values.
            `timestamp` is UTC time stamp of the status; it's current time by default.
            `telemetry` is a list (maybe empty) of (timestamp, metric, value) triplets.
        """
        (status, timestamp, _) = result = super().status()
        if not status.is_ready():
            return result
        mock_trial_data = self.get_current_mock_trial_data()
        if mock_trial_data.status.sleep:
            _LOG.debug("Sleeping for %s seconds", mock_trial_data.status.sleep)
            time.sleep(mock_trial_data.status.sleep)
        if mock_trial_data.status.exception:
            raise RuntimeError(
                f"Mock trial data status exception: {mock_trial_data.status.exception}"
            )
        if mock_trial_data.status.metrics is None:
            # If no metrics are provided, generate them.
            # Note: we don't save these in the mock trial data as they may need
            # to change to preserve backwards compatibility with previous tests.
            metrics = self._produce_metrics(self._status_random)
        else:
            # If metrics are provided, use them.
            # Note: current implementation uses the same metrics for all status
            # calls of this trial.
            metrics = mock_trial_data.status.metrics
        return (
            mock_trial_data.status.status,
            timestamp,
            [(timestamp, metric, score) for (metric, score) in metrics.items()],
        )

    @staticmethod
    def _normalized(tunable: Tunable) -> float:
        """
        Get the NORMALIZED value of a tunable.

        That is, map current value to the [0, 1] range.
        """
        val = None
        if tunable.is_categorical:
            val = tunable.categories.index(tunable.category) / float(len(tunable.categories) - 1)
        elif tunable.is_numerical:
            val = (tunable.numerical_value - tunable.range[0]) / float(
                tunable.range[1] - tunable.range[0]
            )
        else:
            raise ValueError("Invalid parameter type: " + tunable.type)
        # Explicitly clip the value in case of numerical errors.
        ret: float = numpy.clip(val, 0, 1)
        return ret
