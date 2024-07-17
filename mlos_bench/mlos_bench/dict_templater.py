#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Simple class to help with nested dictionary $var templating."""

from copy import deepcopy
from string import Template
from typing import Any, Dict, Optional

from mlos_bench.os_environ import environ


class DictTemplater:  # pylint: disable=too-few-public-methods
    """Simple class to help with nested dictionary $var templating."""

    def __init__(self, source_dict: Dict[str, Any]):
        """
        Initialize the templater.

        Parameters
        ----------
        source_dict : Dict[str, Any]
            The template dict to use for source variables.
        """
        # A copy of the initial data structure we were given with templates intact.
        self._template_dict = deepcopy(source_dict)
        # The source/target dictionary to expand.
        self._dict: Dict[str, Any] = {}

    def expand_vars(
        self,
        *,
        extra_source_dict: Optional[Dict[str, Any]] = None,
        use_os_env: bool = False,
    ) -> Dict[str, Any]:
        """
        Expand the template variables in the destination dictionary.

        Parameters
        ----------
        extra_source_dict : Dict[str, Any]
            An optional extra source dictionary to use for expansion.
        use_os_env : bool
            Whether to use the os environment variables a final fallback for expansion.

        Returns
        -------
        Dict[str, Any]
            The expanded dictionary.
        """
        self._dict = deepcopy(self._template_dict)
        self._dict = self._expand_vars(self._dict, extra_source_dict, use_os_env)
        assert isinstance(self._dict, dict)
        return self._dict

    def _expand_vars(
        self,
        value: Any,
        extra_source_dict: Optional[Dict[str, Any]],
        use_os_env: bool,
    ) -> Any:
        """Recursively expand $var strings in the currently operating dictionary."""
        if isinstance(value, str):
            # First try to expand all $vars internally.
            value = Template(value).safe_substitute(self._dict)
            # Next, if there are any left, try to expand them from the extra source dict.
            if extra_source_dict:
                value = Template(value).safe_substitute(extra_source_dict)
            # Finally, fallback to the os environment.
            if use_os_env:
                value = Template(value).safe_substitute(dict(environ))
        elif isinstance(value, dict):
            # Note: we use a loop instead of dict comprehension in order to
            # allow secondary expansion of subsequent values immediately.
            for key, val in value.items():
                value[key] = self._expand_vars(val, extra_source_dict, use_os_env)
        elif isinstance(value, list):
            value = [self._expand_vars(val, extra_source_dict, use_os_env) for val in value]
        elif isinstance(value, (int, float, bool)) or value is None:
            return value
        else:
            raise ValueError(f"Unexpected type {type(value)} for value {value}")
        return value
