#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for sanitize_conf utility function.

Tests cover obfuscation of sensitive keys and recursive sanitization.
"""
from mlos_bench.util import sanitize_config


def test_sanitize_config_simple() -> None:
    """Test sanitization of a simple configuration dictionary."""
    config = {
        "username": "user1",
        "password": "mypassword",
        "token": "abc123",
        "api_key": "key",
        "secret": "shh",
        "other": 42,
    }
    sanitized = sanitize_config(config)
    assert isinstance(sanitized, dict)
    assert sanitized["username"] == "user1"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["secret"] == "[REDACTED]"
    assert sanitized["other"] == 42


def test_sanitize_config_nested() -> None:
    """Test sanitization of nested dictionaries."""
    config = {
        "outer": {
            "password": "pw",
            "inner": {"token": "tok", "foo": "bar"},
        },
        "api_key": "key",
    }
    sanitized = sanitize_config(config)
    assert isinstance(sanitized, dict)
    assert sanitized["outer"]["password"] == "[REDACTED]"
    assert sanitized["outer"]["inner"]["token"] == "[REDACTED]"
    assert sanitized["outer"]["inner"]["foo"] == "bar"
    assert sanitized["api_key"] == "[REDACTED]"


def test_sanitize_config_no_sensitive_keys() -> None:
    """Test that no changes are made if no sensitive keys are present."""
    config = {"foo": 1, "bar": {"baz": 2}}
    sanitized = sanitize_config(config)
    assert sanitized == config


def test_sanitize_config_mixed_types() -> None:
    """Test sanitization with mixed types including lists and dicts."""
    config = {
        "password": None,
        "token": 123,
        "secret": ["a", "b"],
        "api_key": {"nested": "val"},
    }
    sanitized = sanitize_config(config)
    assert isinstance(sanitized, dict)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["secret"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"


def test_sanitize_config_empty() -> None:
    """Test sanitization of an empty configuration."""
    config = {}
    sanitized = sanitize_config(config)
    assert sanitized == config  # Should remain empty dictionary


def test_sanitize_array() -> None:
    """Test sanitization of an array with sensitive keys."""
    config = [
        {"username": "user1", "password": "pass1"},
        {"username": "user2", "password": "pass2"},
    ]
    sanitized = sanitize_config(config)
    assert isinstance(sanitized, list)
    assert len(sanitized) == 2
    assert sanitized[0]["username"] == "user1"
    assert sanitized[0]["password"] == "[REDACTED]"
    assert sanitized[1]["username"] == "user2"
    assert sanitized[1]["password"] == "[REDACTED]"


def test_sanitize_config_with_non_string_values() -> None:
    """Test sanitization with non-string values."""
    config = {
        "int_value": 42,
        "float_value": 3.14,
        "bool_value": True,
        "none_value": None,
        "list_value": [1, "password", 3],
        "dict_value": {"key": "value"},
    }
    sanitized = sanitize_config(config)
    assert isinstance(sanitized, dict)
    assert sanitized["int_value"] == 42
    assert sanitized["float_value"] == 3.14
    assert sanitized["bool_value"] is True
    assert sanitized["none_value"] is None
    assert sanitized["list_value"] == [1, "password", 3]  # don't redact raw strings
    assert sanitized["dict_value"] == {"key": "value"}
