#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper functions for config example loading tests.
"""

from typing import List

import os
import sys

from mlos_bench.util import path_join

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


BUILTIN_TEST_CONFIG_PATH = str(files("mlos_bench.tests.config").joinpath("")).replace("\\", "/")


def locate_config_examples(config_examples_dir: str) -> List[str]:
    """Locates all config examples in the given directory.

    Parameters
    ----------
    config_examples_dir: str
        Path to the directory containing config examples.

    Returns
    -------
    config_examples: List[str]
        List of paths to config examples.
    """
    assert os.path.isdir(config_examples_dir)
    config_examples = []
    for root, _, _files in os.walk(config_examples_dir):
        for file in _files:
            if file.endswith(".json") or file.endswith(".jsonc"):
                config_examples.append(path_join(root, file))
    return config_examples
