#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for helper functions to lookup and load configs.
"""

from typing import List, Optional, Union, Protocol, runtime_checkable


@runtime_checkable
class SupportsConfigLoading(Protocol):
    """
    Protocol interface for helper functions to lookup and load configs.
    """

    def resolve_path(self, file_path: str,
                     extra_paths: Optional[List[str]] = None) -> str:
        """
        Prepend the suitable `_config_path` to `path` if the latter is not absolute.
        If `_config_path` is `None` or `path` is absolute, return `path` as is.

        Parameters
        ----------
        file_path : str
            Path to the input config file.
        extra_paths : List[str]
            Additional directories to prepend to the list of search paths.

        Returns
        -------
        path : str
            An actual path to the config or script.
        """

    def load_config(self, json_file_name: str) -> Union[dict, List[dict]]:
        """
        Load JSON config file. Search for a file relative to `_config_path`
        if the input path is not absolute.
        This method is exported to be used as a service.

        Parameters
        ----------
        json_file_name : str
            Path to the input config file.

        Returns
        -------
        config : Union[dict, List[dict]]
            Free-format dictionary that contains the configuration.
        """
