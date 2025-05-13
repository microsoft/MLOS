"""
Unit tests for the :py:class:`mlos_bench.environments.status.Status` class.

Tests the :py:meth:`mlos_bench.environments.status.Status.from_str` static method
for correct parsing of both numeric and string representations of each Status,
as well as handling of invalid input.
"""

from typing import Any

import pytest

from mlos_bench.environments.status import Status

@pytest.mark.parametrize(
    ["input_str", "expected_status"],
    [
        ("UNKNOWN", Status.UNKNOWN),
        ("0", Status.UNKNOWN),
        ("PENDING", Status.PENDING),
        ("1", Status.PENDING),
        ("READY", Status.READY),
        ("2", Status.READY),
        ("RUNNING", Status.RUNNING),
        ("3", Status.RUNNING),
        ("SUCCEEDED", Status.SUCCEEDED),
        ("4", Status.SUCCEEDED),
        ("CANCELED", Status.CANCELED),
        ("5", Status.CANCELED),
        ("FAILED", Status.FAILED),
        ("6", Status.FAILED),
        ("TIMED_OUT", Status.TIMED_OUT),
        ("7", Status.TIMED_OUT),
        (" TIMED_OUT ", Status.TIMED_OUT),
    ]
)
def test_status_from_str_valid(input_str: str, expected_status: Status) -> None:
    """
    Test :py:meth:`Status.from_str` with valid string and numeric representations.

    Parameters
    ----------
    input_str : str
        String representation of the status.
    expected_status : Status
        Expected Status enum value.
    """
    assert (
        Status.from_str(input_str) == expected_status
    ), f"Expected {expected_status} for input: {input_str}"
    # Check lowercase representation
    assert (
        Status.from_str(input_str.lower()) == expected_status
    ), f"Expected {expected_status} for input: {input_str.lower()}"
    if input_str.isdigit():
        # Also test the numeric representation
        assert (
            Status.from_str(int(input_str)) == expected_status  # type: ignore
        ), f"Expected {expected_status} for input: {int(input_str)}"


@pytest.mark.parametrize(
    "invalid_input",
    [
        "UNKNOWABLE",
        "8",
        "-1",
        "successful",
        "",
        None,
        123,
        [],
        {},
    ]
)
def test_status_from_str_invalid(invalid_input: Any) -> None:
    """
    Test :py:meth:`Status.from_str` raises ValueError for invalid input.
    """
    assert (
        Status.from_str(invalid_input) == Status.UNKNOWN
    ), f"Expected Status.UNKNOWN for invalid input: {invalid_input}"
