"""
Helper functions for config example loading tests.
"""

import os

from typing import List


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
    config_examples = []
    for root, _, files in os.walk(config_examples_dir):
        for file in files:
            if file.endswith(".json") or file.endswith(".jsonc"):
                config_examples.append(os.path.join(root, file))
    return config_examples
