#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests various other test scenarios with alternative default (un-named) TZ info."""

import os
import sys
from subprocess import run
from typing import Optional

import pytest

from mlos_bench.tests import ZONE_NAMES

DIRNAME = os.path.dirname(__file__)
TZ_TEST_FILES = [
    DIRNAME + "/environments/local/composite_local_env_test.py",
    DIRNAME + "/environments/local/local_env_telemetry_test.py",
    DIRNAME + "/storage/exp_load_test.py",
    DIRNAME + "/storage/trial_telemetry_test.py",
]


@pytest.mark.skipif(sys.platform == "win32", reason="TZ environment variable is a UNIXism")
@pytest.mark.parametrize(("tz_name"), ZONE_NAMES)
@pytest.mark.parametrize(("test_file"), TZ_TEST_FILES)
def test_trial_telemetry_alt_tz(tz_name: Optional[str], test_file: str) -> None:
    """Run the tests under alternative default (un-named) TZ info."""
    env = os.environ.copy()
    if tz_name is None:
        env.pop("TZ", None)
    else:
        env["TZ"] = tz_name
    cmd = run(
        [sys.executable, "-m", "pytest", "-n0", test_file],
        env=env,
        capture_output=True,
        check=False,
    )
    if cmd.returncode != 0:
        print(cmd.stdout.decode())
        print(cmd.stderr.decode())
        raise AssertionError(
            f"Test(s) failed: # TZ='{tz_name}' '{sys.executable}' -m pytest -n0 '{test_file}'"
        )
