#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.
Used to make mypy happy about multiple conftest.py modules.
"""

from typing import Optional

import socket
import shutil

import pytest

from mlos_bench.util import get_class_from_name


# A decorator for tests that require docker.
DOCKER = shutil.which('docker')
requires_docker = pytest.mark.skipif(not DOCKER, reason='Docker is not available on this system.')

# A common seed to use to avoid tracking down race conditions and intermingling
# issues of seeds across tests that run in non-deterministic parallel orders.
SEED = 42

# import numpy as np
# np.random.seed(SEED)


def try_resolve_class_name(class_name: Optional[str]) -> Optional[str]:
    """
    Gets the full class name from the given name or None on error.
    """
    if class_name is None:
        return None
    try:
        the_class = get_class_from_name(class_name)
        return the_class.__module__ + "." + the_class.__name__
    except (ValueError, AttributeError, ModuleNotFoundError, ImportError):
        return None


def check_class_name(obj: object, expected_class_name: str) -> bool:
    """
    Compares the class name of the given object with the given name.
    """
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


def resolve_host_name(host: str) -> str:
    """
    Resolves the host name to an IP address.

    Parameters
    ----------
    host : str

    Returns
    -------
    str
    """
    return socket.gethostbyname(host)
