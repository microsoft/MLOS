#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol representing a bound method."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BoundMethod(Protocol):
    """A callable method bound to an object."""

    # pylint: disable=too-few-public-methods
    # pylint: disable=unnecessary-ellipsis

    @property
    def __self__(self) -> Any:
        """The self object of the bound method."""
        ...

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the bound method."""
        ...
