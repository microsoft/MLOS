#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for Service method registering.
"""

from mlos_bench.services.base_service import Service

from mlos_bench.tests.services.mock_service import SupportsSomeMethod, MockServiceBase, MockServiceChild


def test_service_method_register_without_constructor() -> None:
    """
    Test registering a method without a constructor.
    """
    some_base_service = MockServiceBase()
    some_child_service = MockServiceChild()

    # create a mixin service that registers the base service methods
    mixin_service = Service()
    mixin_service.register(some_base_service.export())

    # pylint complains if we try to just assert this directly
    # somehow having it in a different scope makes a difference
    if isinstance(mixin_service, SupportsSomeMethod):
        assert mixin_service.some_method() == f"{some_base_service}: base.some_method"
        assert mixin_service.some_other_method() == f"{some_base_service}: base.some_other_method"

        # register the child service
        mixin_service.register(some_child_service.export())
        # check that the inheritance works as expected
        assert mixin_service.some_method() == f"{some_child_service}: child.some_method"
        assert mixin_service.some_other_method() == f"{some_child_service}: base.some_other_method"
    else:
        assert False
