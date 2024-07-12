#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.

Used to make mypy happy about multiple conftest.py modules.
"""
import filecmp
import os
import shutil
import socket
from datetime import tzinfo
from logging import debug, warning
from subprocess import run
from typing import List, Optional

import pytest
import pytz

from mlos_bench.util import get_class_from_name, nullable

ZONE_NAMES = [
    # Explicit time zones.
    "UTC",
    "America/Chicago",
    "America/Los_Angeles",
    # Implicit local time zone.
    None,
]
ZONE_INFO: List[Optional[tzinfo]] = [
    nullable(pytz.timezone, zone_name) for zone_name in ZONE_NAMES
]


# A decorator for tests that require docker.
# Use with @requires_docker above a test_...() function.
DOCKER = shutil.which("docker")
if DOCKER:
    cmd = run(
        "docker builder inspect default || docker buildx inspect default",
        shell=True,
        check=False,
        capture_output=True,
    )
    stdout = cmd.stdout.decode()
    if cmd.returncode != 0 or not any(
        line for line in stdout.splitlines() if "Platform" in line and "linux" in line
    ):
        debug("Docker is available but missing support for targeting linux platform.")
        DOCKER = None
requires_docker = pytest.mark.skipif(
    not DOCKER,
    reason="Docker with Linux support is not available on this system.",
)

# A decorator for tests that require ssh.
# Use with @requires_ssh above a test_...() function.
SSH = shutil.which("ssh")
requires_ssh = pytest.mark.skipif(not SSH, reason="ssh is not available on this system.")

# A common seed to use to avoid tracking down race conditions and intermingling
# issues of seeds across tests that run in non-deterministic parallel orders.
SEED = 42

# import numpy as np
# np.random.seed(SEED)


def try_resolve_class_name(class_name: Optional[str]) -> Optional[str]:
    """Gets the full class name from the given name or None on error."""
    if class_name is None:
        return None
    try:
        the_class = get_class_from_name(class_name)
        return the_class.__module__ + "." + the_class.__name__
    except (ValueError, AttributeError, ModuleNotFoundError, ImportError):
        return None


def check_class_name(obj: object, expected_class_name: str) -> bool:
    """Compares the class name of the given object with the given name."""
    full_class_name = obj.__class__.__module__ + "." + obj.__class__.__name__
    return full_class_name == try_resolve_class_name(expected_class_name)


def check_socket(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Test to see if a socket is open.

    Parameters
    ----------
    host : str
    port : int
    timeout: float

    Returns
    -------
    bool
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)  # seconds
        result = sock.connect_ex((host, port))
        return result == 0


def resolve_host_name(host: str) -> Optional[str]:
    """
    Resolves the host name to an IP address.

    Parameters
    ----------
    host : str

    Returns
    -------
    str
    """
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def are_dir_trees_equal(dir1: str, dir2: str) -> bool:
    """
    Compare two directories recursively. Files in each directory are assumed to be equal
    if their names and contents are equal.

    @param dir1: First directory path @param dir2: Second directory path

    @return: True if the directory trees are the same and     there were no errors while
    accessing the directories or files,     False otherwise.
    """
    # See Also: https://stackoverflow.com/a/6681395
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (
        len(dirs_cmp.left_only) > 0
        or len(dirs_cmp.right_only) > 0
        or len(dirs_cmp.funny_files) > 0
    ):
        warning(
            (
                f"Found differences in dir trees {dir1}, {dir2}:\n"
                f"{dirs_cmp.diff_files}\n{dirs_cmp.funny_files}"
            )
        )
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch) > 0 or len(errors) > 0:
        warning(f"Found differences in files:\n{mismatch}\n{errors}")
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True
