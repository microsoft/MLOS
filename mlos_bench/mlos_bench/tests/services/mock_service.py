#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Basic MockService for testing.

See Also: test_service_method_registering.py
"""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from mlos_bench.services.base_service import Service


@runtime_checkable
class SupportsSomeMethod(Protocol):
    """Protocol for some_method."""

    def some_method(self) -> str:
        """some_method."""

    def some_other_method(self) -> str:
        """some_other_method."""


class MockServiceBase(Service, SupportsSomeMethod):
    """A base service class for testing."""

    def __init__(
        self,
        config: dict | None = None,
        global_config: dict | None = None,
        parent: Service | None = None,
        methods: dict[str, Callable] | list[Callable] | None = None,
    ) -> None:
        super().__init__(
            config,
            global_config,
            parent,
            self.merge_methods(
                methods,
                [
                    self.some_method,
                    self.some_other_method,
                ],
            ),
        )

    def some_method(self) -> str:
        """some_method."""
        return f"{self}: base.some_method"

    def some_other_method(self) -> str:
        """some_other_method."""
        return f"{self}: base.some_other_method"


class MockServiceChild(MockServiceBase, SupportsSomeMethod):
    """A child service class for testing."""

    # Intentionally includes no constructor.

    def some_method(self) -> str:
        """some_method."""
        return f"{self}: child.some_method"
