#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.
Used to make mypy happy about multiple conftest.py modules.
"""

from typing import Optional, Set

from mlos_bench.util import get_class_from_name


def get_all_subclasses(cls: type) -> Set[type]:
    """
    Gets all of the subclasses of the given class.
    Useful for dynamically enumerating expected test cases.
    """
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)])


def try_resolve_class_name(class_name: str) -> Optional[str]:
    """
    Gets the full class name from the given name or None on error.
    """
    try:
        the_class = get_class_from_name(class_name)
        return the_class.__module__ + "." + the_class.__name__
    except (ValueError, AttributeError, ModuleNotFoundError, ImportError):
        return None
