#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Provides some pytest configuration overrides for both modules.
"""

# Note: This file is named conftest.py so that pytest picks it up automatically
# without the need to adjust PYTHONPATH or sys.path as much.

from warnings import warn
from tempfile import mkdtemp

import os
import shutil

import pytest
from xdist.workermanage import WorkerController


def is_master(config: pytest.Config) -> bool:
    """
    True if the code running the given pytest.config object is running in a
    xdist master node or not running xdist at all.
    """
    return not hasattr(config, "workerinput")


def pytest_configure(config: pytest.Config) -> None:
    """
    Add some additional (global) configuration steps for pytest.
    """
    # Workaround some issues loading emukit in certain environments.
    if os.environ.get("DISPLAY", None):
        try:
            import matplotlib  # pylint: disable=import-outside-toplevel

            matplotlib.rcParams["backend"] = "agg"
            if is_master(config) or dict(getattr(config, "workerinput", {}))["workerid"] == "gw0":
                # Only warn once.
                warn(
                    UserWarning(
                        (
                            "DISPLAY environment variable is set, "
                            "which can cause problems in some setups (e.g. WSL). "
                            f"Adjusting matplotlib backend to '{matplotlib.rcParams['backend']}' "
                            "to compensate."
                        )
                    )
                )
        except ImportError:
            pass

    # Create a temporary directory for sharing files between master and worker nodes.
    if is_master(config):
        # Add it to the config so that it can passed to the worker nodes.
        setattr(config, "shared_temp_dir", mkdtemp())


def pytest_configure_node(node: WorkerController) -> None:
    """
    Xdist hook used to inform workers of the location of the shared temp dir.
    """
    workerinput: dict = getattr(node, "workerinput")
    workerinput["shared_temp_dir"] = getattr(node.config, "shared_temp_dir")


@pytest.fixture(scope="session")
def shared_temp_dir(request: pytest.FixtureRequest) -> str:
    """
    Returns a unique and temporary directory which can be shared by
    master or worker nodes in xdist runs.
    """
    if is_master(request.config):
        return str(getattr(request.config, "shared_temp_dir"))
    else:
        workerinput: dict = getattr(request.config, "workerinput")
        return str(workerinput["shared_temp_dir"])


def pytest_unconfigure(config: pytest.Config) -> None:
    """
    Called after all tests have completed.
    """
    if is_master(config):
        shared_tmp_dir = getattr(config, "shared_temp_dir", None)
        if shared_tmp_dir:
            shutil.rmtree(str(shared_tmp_dir))


@pytest.fixture(scope="session")
def short_testrun_uid(testrun_uid: str) -> str:
    """
    Shorten the unique test run id that xdist provides so we can use it with
    other systems (e.g., docker).
    """
    return testrun_uid[0:8]
