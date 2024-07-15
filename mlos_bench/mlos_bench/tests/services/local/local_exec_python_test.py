#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for LocalExecService to run Python scripts locally."""

import json
from typing import Any, Dict

import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name


@pytest.fixture
def local_exec_service() -> LocalExecService:
    """Test fixture for LocalExecService."""
    return LocalExecService(parent=ConfigPersistenceService())


def test_run_python_script(local_exec_service: LocalExecService) -> None:
    """Run a Python script using a local_exec service."""
    input_file = "./input-params.json"
    meta_file = "./input-params-meta.json"
    output_file = "./config-kernel.sh"

    # Tunable parameters to save in JSON
    params: Dict[str, TunableValue] = {
        "sched_migration_cost_ns": 40000,
        "sched_granularity_ns": 800000,
    }

    # Tunable parameters metadata
    params_meta: Dict[str, Any] = {
        "sched_migration_cost_ns": {"name_prefix": "/proc/sys/kernel/"},
        "sched_granularity_ns": {"name_prefix": "/proc/sys/kernel/"},
    }

    with local_exec_service.temp_dir_context() as temp_dir:

        with open(path_join(temp_dir, input_file), "wt", encoding="utf-8") as fh_input:
            json.dump(params, fh_input)

        with open(path_join(temp_dir, meta_file), "wt", encoding="utf-8") as fh_meta:
            json.dump(params_meta, fh_meta)

        script_path = local_exec_service.config_loader_service.resolve_path(
            "environments/os/linux/runtime/scripts/local/generate_kernel_config_script.py"
        )

        (return_code, _stdout, stderr) = local_exec_service.local_exec(
            [f"{script_path} {input_file} {meta_file} {output_file}"],
            cwd=temp_dir,
            env=params,
        )

        assert stderr.strip() == ""
        assert return_code == 0
        # assert stdout.strip() == ""

        with open(path_join(temp_dir, output_file), "rt", encoding="utf-8") as fh_output:
            assert [ln.strip() for ln in fh_output.readlines()] == [
                'echo "40000" > /proc/sys/kernel/sched_migration_cost_ns',
                'echo "800000" > /proc/sys/kernel/sched_granularity_ns',
            ]
