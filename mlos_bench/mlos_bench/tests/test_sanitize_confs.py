#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for sanitize_conf utility function.

Tests cover obfuscation of sensitive keys and recursive sanitization.
"""
import json5

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
    config: dict = {}
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


def test_sanitize_config_json_string() -> None:
    """Test sanitization when input is a JSON string."""
    config = {
        "username": "user1",
        "password": "mypassword",
        "token": "abc123",
        "nested": {"api_key": "key", "other": 1},
        "list": [{"secret": "shh"}, {"foo": "bar"}],
    }
    config_json = json5.dumps(config)
    sanitized = sanitize_config(config_json)
    # Should return a JSON string
    assert isinstance(sanitized, str)
    sanitized_dict = json5.loads(sanitized)
    assert isinstance(sanitized_dict, dict)
    assert sanitized_dict["username"] == "user1"
    assert sanitized_dict["password"] == "[REDACTED]"
    assert sanitized_dict["token"] == "[REDACTED]"
    assert sanitized_dict["nested"]["api_key"] == "[REDACTED]"
    assert sanitized_dict["nested"]["other"] == 1
    assert sanitized_dict["list"][0]["secret"] == "[REDACTED]"
    assert sanitized_dict["list"][1]["foo"] == "bar"


def test_sanitize_config_invalid_json_string() -> None:
    """Test sanitization with an invalid JSON string input."""
    invalid_json = '{"username": "user1", "password": "pw"'  # missing closing brace
    assert sanitize_config(invalid_json) == invalid_json


def test_sanitize_config_json5_string() -> None:
    """Test sanitization with an invalid JSON5 string input."""
    invalid_json = '{"username": "user1", "password": "pw", }'  # with trailing comma
    # Should return processed json as string
    sanitized = sanitize_config(invalid_json)
    assert isinstance(sanitized, str)
    sanitize_dict = json5.loads(sanitized)
    assert isinstance(sanitize_dict, dict)
    assert len(sanitize_dict) == 2
    assert sanitize_dict["username"] == "user1"
    assert sanitize_dict["password"] == "[REDACTED]"


def test_sanitize_config_json_string_no_sensitive_keys() -> None:
    """Test sanitization of a JSON string with no sensitive keys."""
    config = {"foo": 1, "bar": {"baz": 2}}
    config_json = json5.dumps(config)
    sanitized = sanitize_config(config_json)
    assert isinstance(sanitized, str)
    sanitized_dict = json5.loads(sanitized)
    assert sanitized_dict == config
