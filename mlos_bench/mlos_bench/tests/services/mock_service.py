#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Basic MockService for testing.

See Also: test_service_method_registering.py
"""

from typing import Callable, Dict, List, Optional, Protocol, Union, runtime_checkable

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
        config: Optional[dict] = None,
        global_config: Optional[dict] = None,
        parent: Optional[Service] = None,
        methods: Optional[Union[Dict[str, Callable], List[Callable]]] = None,
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
