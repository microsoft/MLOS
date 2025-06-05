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
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["secret"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
