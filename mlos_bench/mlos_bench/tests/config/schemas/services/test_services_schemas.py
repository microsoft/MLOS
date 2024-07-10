#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for service schema validation."""

from os import path
from typing import Any, Dict, List

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.base_service import Service
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.temp_dir_context import TempDirContextService
from mlos_bench.services.remote.azure.azure_deployment_services import (
    AzureDeploymentService,
)
from mlos_bench.services.remote.ssh.ssh_service import SshService
from mlos_bench.tests import try_resolve_class_name
from mlos_bench.tests.config.schemas import (
    check_test_case_against_schema,
    check_test_case_config_with_extra_param,
    get_schema_test_cases,
)
from mlos_core.tests import get_all_concrete_subclasses

# General testing strategy:
# - hand code a set of good/bad configs (useful to test editor schema checking)
# - enumerate and try to check that we've covered all the cases
# - for each config, load and validate against expected schema

TEST_CASES = get_schema_test_cases(path.join(path.dirname(__file__), "test-cases"))


# Dynamically enumerate some of the cases we want to make sure we cover.

NON_CONFIG_SERVICE_CLASSES = {
    # configured thru the launcher cli args
    ConfigPersistenceService,
    # ABCMeta abstract class, but no good way to test that dynamically in Python.
    TempDirContextService,
    # ABCMeta abstract base class
    AzureDeploymentService,
    # ABCMeta abstract base class
    SshService,
}

expected_service_class_names = [
    subclass.__module__ + "." + subclass.__name__
    for subclass in get_all_concrete_subclasses(Service, pkg_name="mlos_bench")
    if subclass not in NON_CONFIG_SERVICE_CLASSES
]
assert expected_service_class_names


# Do the full cross product of all the test cases and all the Service types.
@pytest.mark.parametrize("test_case_subtype", sorted(TEST_CASES.by_subtype))
@pytest.mark.parametrize("service_class", expected_service_class_names)
def test_case_coverage_mlos_bench_service_type(test_case_subtype: str, service_class: str) -> None:
    """Checks to see if there is a given type of test case for the given mlos_bench
    Service type.
    """
    for test_case in TEST_CASES.by_subtype[test_case_subtype].values():
        config_list: List[Dict[str, Any]]
        if not isinstance(test_case.config, dict):
            continue  # type: ignore[unreachable]
        if "class" not in test_case.config:
            config_list = test_case.config["services"]
        else:
            config_list = [test_case.config]
        for config in config_list:
            if try_resolve_class_name(config.get("class")) == service_class:
                return
    raise NotImplementedError(
        f"Missing test case for subtype {test_case_subtype} for service class {service_class}"
    )


# Now we actually perform all of those validation tests.


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_path))
def test_service_configs_against_schema(test_case_name: str) -> None:
    """Checks that the service config validates against the schema."""
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.SERVICE)
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.UNIFIED)


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_type["good"]))
def test_service_configs_with_extra_param(test_case_name: str) -> None:
    """Checks that the service config fails to validate if extra params are present in
    certain places.
    """
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.SERVICE,
    )
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.UNIFIED,
    )
