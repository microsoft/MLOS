#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.
Used to make mypy happy about multiple conftest.py modules.
"""

from typing import Optional

import numpy as np

from mlos_bench.util import get_class_from_name


# A common seed to use to avoid tracking down race conditions and intermingling
# issues of seeds across tests that run in non-deterministic parallel orders.
SEED = 42
np.random.seed(SEED)


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
