#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
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
    ],
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
    ],
)
def test_status_from_str_invalid(invalid_input: Any) -> None:
    """Test :py:meth:`Status.from_str` returns :py:attr:`Status.UNKNOWN` for invalid
    input.
    """
    assert (
        Status.from_str(invalid_input) == Status.UNKNOWN
    ), f"Expected Status.UNKNOWN for invalid input: {invalid_input}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, True),
        (Status.READY, True),
        (Status.RUNNING, True),
        (Status.SUCCEEDED, True),
        (Status.CANCELED, False),
        (Status.FAILED, False),
        (Status.TIMED_OUT, False),
    ],
)
def test_status_is_good(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_good` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_good method.
    """
    assert status.is_good() == expected_result, f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, False),
        (Status.READY, False),
        (Status.RUNNING, False),
        (Status.SUCCEEDED, True),
        (Status.CANCELED, True),
        (Status.FAILED, True),
        (Status.TIMED_OUT, True),
    ],
)
def test_status_is_completed(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_completed` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_completed method.
    """
    assert (
        status.is_completed() == expected_result
    ), f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, True),
        (Status.READY, False),
        (Status.RUNNING, False),
        (Status.SUCCEEDED, False),
        (Status.CANCELED, False),
        (Status.FAILED, False),
        (Status.TIMED_OUT, False),
    ],
)
def test_status_is_pending(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_pending` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_pending method.
    """
    assert (
        status.is_pending() == expected_result
    ), f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, False),
        (Status.READY, True),
        (Status.RUNNING, False),
        (Status.SUCCEEDED, False),
        (Status.CANCELED, False),
        (Status.FAILED, False),
        (Status.TIMED_OUT, False),
    ],
)
def test_status_is_ready(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_ready` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_ready method.
    """
    assert status.is_ready() == expected_result, f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, False),
        (Status.READY, False),
        (Status.RUNNING, True),
        (Status.SUCCEEDED, False),
        (Status.CANCELED, False),
        (Status.FAILED, False),
        (Status.TIMED_OUT, False),
    ],
)
def test_status_is_running(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_running` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_running method.
    """
    assert (
        status.is_running() == expected_result
    ), f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, False),
        (Status.READY, False),
        (Status.RUNNING, False),
        (Status.SUCCEEDED, True),
        (Status.CANCELED, False),
        (Status.FAILED, False),
        (Status.TIMED_OUT, False),
    ],
)
def test_status_is_succeeded(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_succeeded` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_succeeded method.
    """
    assert (
        status.is_succeeded() == expected_result
    ), f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, False),
        (Status.READY, False),
        (Status.RUNNING, False),
        (Status.SUCCEEDED, False),
        (Status.CANCELED, True),
        (Status.FAILED, False),
        (Status.TIMED_OUT, False),
    ],
)
def test_status_is_canceled(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_canceled` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_canceled method.
    """
    assert (
        status.is_canceled() == expected_result
    ), f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, False),
        (Status.READY, False),
        (Status.RUNNING, False),
        (Status.SUCCEEDED, False),
        (Status.CANCELED, False),
        (Status.FAILED, True),
        (Status.TIMED_OUT, False),
    ],
)
def test_status_is_failed(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_failed` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_failed method.
    """
    assert (
        status.is_failed() == expected_result
    ), f"Expected {expected_result} for status: {status}"


@pytest.mark.parametrize(
    ["status", "expected_result"],
    [
        (Status.UNKNOWN, False),
        (Status.PENDING, False),
        (Status.READY, False),
        (Status.RUNNING, False),
        (Status.SUCCEEDED, False),
        (Status.CANCELED, False),
        (Status.FAILED, False),
        (Status.TIMED_OUT, True),
    ],
)
def test_status_is_timed_out(status: Status, expected_result: bool) -> None:
    """
    Test :py:meth:`Status.is_timed_out` for various statuses.

    Parameters
    ----------
    status : Status
        The Status enum value to test.
    expected_result : bool
        Expected result of the is_timed_out method.
    """
    assert (
        status.is_timed_out() == expected_result
    ), f"Expected {expected_result} for status: {status}"
