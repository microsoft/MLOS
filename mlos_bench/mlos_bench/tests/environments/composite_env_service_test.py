#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Check how the services get inherited and overridden in child environments.
"""
import os

import pytest

from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name


@pytest.fixture
def composite_env(tunable_groups: TunableGroups) -> CompositeEnv:
    """
    Test fixture for CompositeEnv with services included on multiple levels.
    """
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
                }
            ]
        },
        tunables=tunable_groups,
        service=LocalExecService(
            config={
                "temp_dir": "tmp_global"
            },
            parent=ConfigPersistenceService({
                "config_path": [
                    path_join(os.path.dirname(__file__), "../config", abs_path=True),
                ]
            })
        )
    )


def test_composite_services(composite_env: CompositeEnv) -> None:
    """
    Check that each environment gets its own instance of the services.
    """
    # pylint: disable=protected-access
    with composite_env.children[0]._service.temp_dir_context() as temp_dir:
        assert os.path.samefile(temp_dir, "tmp_global")

    with composite_env.children[1]._service.temp_dir_context() as temp_dir:
        assert os.path.samefile(temp_dir, "tmp_other_2")

    with composite_env.children[2]._service.temp_dir_context() as temp_dir:
        assert os.path.samefile(temp_dir, "tmp_other_3")
