#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.
Used to make mypy happy about multiple conftest.py modules.
"""

from typing import Optional

from mlos_bench.util import get_class_from_name


def try_resolve_class_name(class_name: str) -> Optional[str]:
    """
    Gets the full class name from the given name or None on error.
    """
    try:
        the_class = get_class_from_name(class_name)
        return the_class.__module__ + "." + the_class.__name__
    except (ValueError, AttributeError, ModuleNotFoundError, ImportError):
        return None
