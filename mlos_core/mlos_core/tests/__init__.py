#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Common functions for mlos_core Optimizer tests.
"""

from typing import Set


def get_all_subclasses(cls: type) -> Set[type]:
    """
    Gets all of the subclasses of the given class.
    Useful for dynamically enumerating expected test cases.
    """
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)])
