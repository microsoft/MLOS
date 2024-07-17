#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Helper functions for config example loading tests."""

import os
import sys
from typing import Callable, List, Optional

from mlos_bench.util import path_join

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


BUILTIN_TEST_CONFIG_PATH = str(files("mlos_bench.tests.config").joinpath("")).replace("\\", "/")


def locate_config_examples(
    root_dir: str,
    config_examples_dir: str,
    examples_filter: Optional[Callable[[List[str]], List[str]]] = None,
) -> List[str]:
    """
    Locates all config examples in the given directory.

    Parameters
    ----------
    root_dir : str
        Root dir of the config_examples_dir.
    config_examples_dir: str
        Name to the directory containing config examples.
    examples_filter : callable
        Optional filter to provide on the returned results.

    Returns
    -------
    config_examples: List[str]
        List of paths to config examples.
    """
    if examples_filter is None:
        examples_filter = list
    config_examples_path = path_join(root_dir, config_examples_dir)
    assert os.path.isdir(config_examples_path)
    config_examples = []
    for root, _, dir_files in os.walk(config_examples_path):
        for file in dir_files:
            if file.endswith(".json") or file.endswith(".jsonc"):
                config_examples.append(path_join(root, file))
    return examples_filter(config_examples)
