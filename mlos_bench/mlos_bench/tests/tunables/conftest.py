#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test fixtures for individual Tunable objects."""

import pytest

from mlos_bench.tunables.tunable import Tunable

# pylint: disable=redefined-outer-name
# -- Ignore pylint complaints about pytest references to
# `tunable_groups` fixture as both a function and a parameter.


@pytest.fixture
def tunable_categorical() -> Tunable:
    """
    A test fixture that produces a categorical Tunable object.

    Returns
    -------
    tunable : Tunable
        An instance of a categorical Tunable.
    """
    return Tunable(
        "vmSize",
        {
            "description": "Azure VM size",
            "type": "categorical",
            "default": "Standard_B4ms",
            "values": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"],
        },
    )


@pytest.fixture
def tunable_int() -> Tunable:
    """
    A test fixture that produces an integer Tunable object with limited range.

    Returns
    -------
    tunable : Tunable
        An instance of an integer Tunable.
    """
    return Tunable(
        "kernel_sched_migration_cost_ns",
        {
            "description": "Cost of migrating the thread to another core",
            "type": "int",
            "default": 40000,
            "range": [0, 500000],
            "special": [-1],  # Special value outside of the range
        },
    )


@pytest.fixture
def tunable_float() -> Tunable:
    """
    A test fixture that produces a float Tunable object with limited range.

    Returns
    -------
    tunable : Tunable
        An instance of a float Tunable.
    """
    return Tunable(
        "chaos_monkey_prob",
        {
            "description": "Probability of spontaneous VM shutdown",
            "type": "float",
            "default": 0.01,
            "range": [0, 1],
        },
    )
