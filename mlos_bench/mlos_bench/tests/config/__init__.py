"""
Helper functions for config example loading tests.
"""

from typing import Any, List, Optional

import importlib
import logging
import os

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


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


def load_config_example(config_path: str, config_overrides: Optional[dict] = None) -> Any:
    """Tests loading a config example."""
    config_loader_service = ConfigPersistenceService()
    _LOG.info("Loading config %s", config_path)
    config = config_loader_service.load_config(config_path)
    assert isinstance(config, dict)
    if config_overrides is not None:
        config.update(config_overrides)

    cls_fqn: str = config["class"]
    _LOG.info("Loading %s", cls_fqn)
    module = importlib.import_module(str.join(".", (cls_fqn.split(".")[0:-1])))
    cls = getattr(module, cls_fqn.split(".")[-1])
    assert isinstance(cls, type)

    return config_loader_service.build_generic(
        base_cls=cls,
        tunables=TunableGroups(),
        service=config_loader_service,
        config=config,
    )
