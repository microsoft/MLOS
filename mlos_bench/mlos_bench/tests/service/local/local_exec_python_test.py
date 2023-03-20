#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for LocalExecService to run Python scripts locally.
"""
import os
import json

import pytest

from mlos_bench.service import LocalExecService, ConfigPersistenceService

# pylint: disable=redefined-outer-name


@pytest.fixture
def local_exec_service() -> LocalExecService:
    """
    Test fixture for LocalExecService.
    """
    return LocalExecService(parent=ConfigPersistenceService({
        "config_path": ["mlos_bench/config"]
    }))


def test_run_python_script(local_exec_service: LocalExecService):
    """
    Run a Python script using a local_exec service.
    """
    input_file = "./input-params.json"
    output_file = "./config-kernel.sh"

    # Tunable parameters to save in JSON
    params = {
        "sched_migration_cost_ns": 40000,
        "sched_granularity_ns": 800000
    }

    with local_exec_service.temp_dir_context() as temp_dir:

        with open(os.path.join(temp_dir, input_file), "wt", encoding="utf-8") as fh_input:
            json.dump(params, fh_input)

        (return_code, _stdout, stderr) = local_exec_service.local_exec([
            f"linux-setup/generate_kernel_config_script.py {input_file} {output_file}"
        ], cwd=temp_dir, env=params)

        assert return_code == 0
        # assert stdout.strip() == ""
        assert stderr.strip() == ""

        with open(os.path.join(temp_dir, output_file), "rt", encoding="utf-8") as fh_output:
            assert [ln.strip() for ln in fh_output.readlines()] == [
                'echo "40000" > /proc/sys/kernel/sched_migration_cost_ns',
                'echo "800000" > /proc/sys/kernel/sched_granularity_ns',
            ]
