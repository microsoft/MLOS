#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for Service method registering.
"""

from typing import Protocol, runtime_checkable

from mlos_bench.services.base_service import Service


@runtime_checkable
class SupportsSomeMethod(Protocol):
    """Protocol for some_method"""

    def some_method(self) -> str:
        """some_method"""
        pass


class SomeBaseServiceClass(Service):
    """A base service class for testing."""

    def some_method(self) -> str:
        """some_method"""
        return "SomeBaseServiceClass.some_method"


class SomeChildServiceClass(Service):
    """A child service class for testing."""

    def some_method(self) -> str:
        """some_method"""
        return "SomeChildServiceClass.some_method"


def test_service_method_register_without_constructor() -> None:
    """
    Test registering a method without a constructor.
    """

    some_base_service = SomeBaseServiceClass()
    some_child_service = SomeChildServiceClass()

    mixin_service = Service()
    mixin_service.register(some_base_service.export())

    assert isinstance(mixin_service, SupportsSomeMethod)

    assert mixin_service.some_method() == "SomeBaseServiceClass.some_method"

    mixin_service.register(some_child_service.export())
    assert mixin_service.some_method() == "SomeChildServiceClass.some_method"
