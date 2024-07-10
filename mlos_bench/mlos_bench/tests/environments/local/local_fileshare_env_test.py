#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for passing shell environment variables into LocalEnv scripts."""
import pytest

from mlos_bench.environments.local.local_fileshare_env import LocalFileShareEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.tests.services.remote.mock.mock_fileshare_service import (
    MockFileShareService,
)
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="module")
def mock_fileshare_service() -> MockFileShareService:
    """Create a new mock FileShareService instance."""
    return MockFileShareService(
        config={"fileShareName": "MOCK_FILESHARE"},
        parent=LocalExecService(parent=ConfigPersistenceService()),
    )


@pytest.fixture
def local_fileshare_env(
    tunable_groups: TunableGroups,
    mock_fileshare_service: MockFileShareService,
) -> LocalFileShareEnv:
    """Create a LocalFileShareEnv instance."""
    env = LocalFileShareEnv(
        name="TestLocalFileShareEnv",
        config={
            "const_args": {
                "experiment_id": "EXP_ID",  # Passed into "shell_env_params"
                "trial_id": 222,  # NOT passed into "shell_env_params"
            },
            "tunable_params": ["boot"],
            "shell_env_params": [
                "trial_id",  # From "const_arg"
                "idle",  # From "tunable_params", == "halt"
            ],
            "upload": [
                {
                    "from": "grub.cfg",
                    "to": "$experiment_id/$trial_id/input/grub.cfg",
                },
                {
                    "from": "data_$idle.csv",
                    "to": "$experiment_id/$trial_id/input/data_$idle.csv",
                },
            ],
            "run": ["echo No-op run"],
            "download": [
                {
                    "from": "$experiment_id/$trial_id/$idle/data.csv",
                    "to": "output/data_$idle.csv",
                },
            ],
        },
        tunables=tunable_groups,
        service=mock_fileshare_service,
    )
    return env


def test_local_fileshare_env(
    tunable_groups: TunableGroups,
    mock_fileshare_service: MockFileShareService,
    local_fileshare_env: LocalFileShareEnv,
) -> None:
    """Test that the LocalFileShareEnv correctly expands the `$VAR` variables in the
    upload and download sections of the config.
    """
    with local_fileshare_env as env_context:
        assert env_context.setup(tunable_groups)
        (status, _ts, _output) = env_context.run()
        assert status.is_succeeded()
        assert mock_fileshare_service.get_upload() == [
            ("grub.cfg", "EXP_ID/222/input/grub.cfg"),
            ("data_halt.csv", "EXP_ID/222/input/data_halt.csv"),
        ]
        # NOTE: The "download" section is run twice -- once to check
        # the status of the run, and once to get the final results.
        assert mock_fileshare_service.get_download() == [
            ("EXP_ID/222/halt/data.csv", "output/data_halt.csv"),
            ("EXP_ID/222/halt/data.csv", "output/data_halt.csv"),
        ]
