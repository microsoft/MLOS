#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common functions for mlos_core Optimizer tests."""

from importlib import import_module
from pkgutil import walk_packages
from types import ModuleType
from typing import TypeVar

# A common seed to use to avoid tracking down race conditions and intermingling
# issues of seeds across tests that run in non-deterministic parallel orders.
SEED = 42

T = TypeVar("T")


def get_all_submodules(pkg: ModuleType) -> list[str]:
    """
    Imports all submodules for a package and returns their names.

    Useful for dynamically enumerating subclasses.
    """
    submodules = []
    for _, submodule_name, _ in walk_packages(
        pkg.__path__, prefix=f"{pkg.__name__}.", onerror=lambda x: None
    ):
        submodules.append(submodule_name)
    return submodules


def _get_all_subclasses(cls: type[T]) -> set[type[T]]:
    """
    Gets the set of all of the subclasses of the given class.

    Useful for dynamically enumerating expected test cases.
    """
    return set(cls.__subclasses__()).union(
        s for c in cls.__subclasses__() for s in _get_all_subclasses(c)
    )


def get_all_concrete_subclasses(cls: type[T], pkg_name: str | None = None) -> list[type[T]]:
    """
    Gets a sorted list of all of the concrete subclasses of the given class. Useful for
    dynamically enumerating expected test cases.

    Note: For abstract types, mypy will complain at the call site.
    Use "# type: ignore[type-abstract]" to suppress the warning.
    See Also: https://github.com/python/mypy/issues/4717
    """
    if pkg_name is not None:
        pkg = import_module(pkg_name)
        submodules = get_all_submodules(pkg)
        assert submodules
    return sorted(
        [
            subclass
            for subclass in _get_all_subclasses(cls)
            if not getattr(subclass, "__abstractmethods__", None)
        ],
        key=lambda c: (c.__module__, c.__name__),
    )
