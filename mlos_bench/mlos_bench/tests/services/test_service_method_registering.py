#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for Service method registering."""

import pytest

from mlos_bench.services.base_service import Service
from mlos_bench.tests.services.mock_service import (
    MockServiceBase,
    MockServiceChild,
    SupportsSomeMethod,
)


def test_service_method_register_without_constructor() -> None:
    """Test registering a method without a constructor."""
    # pylint: disable=protected-access
    some_base_service = MockServiceBase()
    some_child_service = MockServiceChild()

    # create a mixin service that registers the base service methods
    mixin_service = Service()

    # Registering service methods inside a context should fail.
    with pytest.raises(AssertionError):
        with mixin_service as service_context:
            service_context.register(some_base_service.export())

    mixin_service.register(some_base_service.export())
    # Make sure the base service instance got tracked registered
    assert mixin_service._services == {some_base_service}

    # pylint complains if we try to just assert this directly
    # somehow having it in a different scope makes a difference
    if isinstance(mixin_service, SupportsSomeMethod):
        assert mixin_service.some_method() == f"{some_base_service}: base.some_method"
        assert mixin_service.some_other_method() == f"{some_base_service}: base.some_other_method"

        # register the child service
        mixin_service.register(some_child_service.export())
        # Make sure the child service instance got tracked registered
        assert mixin_service._services == {some_child_service}
        # check that the inheritance works as expected
        assert mixin_service.some_method() == f"{some_child_service}: child.some_method"
        assert mixin_service.some_other_method() == f"{some_child_service}: base.some_other_method"
    else:
        assert False
