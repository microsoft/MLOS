#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Check how the services get inherited and overridden in child environments."""
import os

import pytest

from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name


@pytest.fixture
def composite_env(tunable_groups: TunableGroups) -> CompositeEnv:
    """Test fixture for CompositeEnv with services included on multiple levels."""
    return CompositeEnv(
        name="Root",
        config={
            "children": [
                {
                    "name": "Env 1 :: tmp_global",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                },
                {
                    "name": "Env 2 :: tmp_other_2",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "include_services": ["services/local/mock/mock_local_exec_service_2.jsonc"],
                },
                {
                    "name": "Env 3 :: tmp_other_3",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "include_services": ["services/local/mock/mock_local_exec_service_3.jsonc"],
                },
            ]
        },
        tunables=tunable_groups,
        service=LocalExecService(
            config={"temp_dir": "_test_tmp_global"},
            parent=ConfigPersistenceService(
                {
                    "config_path": [
                        path_join(os.path.dirname(__file__), "../config", abs_path=True),
                    ]
                }
            ),
        ),
    )


def test_composite_services(composite_env: CompositeEnv) -> None:
    """Check that each environment gets its own instance of the services."""
    for i, path in ((0, "_test_tmp_global"), (1, "_test_tmp_other_2"), (2, "_test_tmp_other_3")):
        service = composite_env.children[i]._service  # pylint: disable=protected-access
        assert service is not None and hasattr(service, "temp_dir_context")
        with service.temp_dir_context() as temp_dir:
            assert os.path.samefile(temp_dir, path)
        os.rmdir(path)
