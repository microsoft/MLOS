#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Common functions for mlos_core Optimizer tests.
"""

from typing import List, Set, Type, TypeVar


T = TypeVar('T')


def _get_all_subclasses(cls: Type[T]) -> Set[Type[T]]:
    """
    Gets the set of all of the subclasses of the given class.
    Useful for dynamically enumerating expected test cases.
    """
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in _get_all_subclasses(c)])


def get_all_concrete_subclasses(cls: Type[T]) -> List[Type[T]]:
    """
    Gets a sorted list of all of the concrete subclasses of the given class.
    Useful for dynamically enumerating expected test cases.

    Note: For abstract types, mypy will complain at the call site.
    Use "# type: ignore[type-abstract]" to suppress the warning.
    See Also: https://github.com/python/mypy/issues/4717
    """
    return sorted([subclass for subclass in _get_all_subclasses(cls) if not getattr(subclass, "__abstractmethods__", None)],
                  key=lambda x: x.__module__ + "." + x.__name__)
