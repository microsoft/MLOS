#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for saving and restoring the telemetry data when host timezone is in a different timezone.
"""

from subprocess import run
import os
import sys
from typing import Optional

import pytest

# pylint: disable=redefined-outer-name


@pytest.mark.skipif(sys.platform == 'win32', reason="sh-like shell only")
@pytest.mark.parametrize(("tz_name"), [None, "America/Chicago", "America/Los_Angeles", "UTC"])
def test_trial_telemetry_alt_tz(tz_name: Optional[str]) -> None:
    """
    Run the trial telemetry tests under alternative default (un-named) TZ info.
    """
    env = os.environ.copy()
    if tz_name is None:
        env.pop("TZ", None)
    else:
        env["TZ"] = tz_name
    cmd = run(
        [sys.executable, "-m", "pytest", "-n0", f"{os.path.dirname(__file__)}/trial_telemetry_test.py"],
        # , "-k", "implicit_local"],
        env=env,
        check=True,
    )
    assert cmd.returncode == 0
