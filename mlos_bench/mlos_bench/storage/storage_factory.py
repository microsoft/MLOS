#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Factory method to create a new Storage instance from configs.
"""

from typing import Any, Optional, List, Dict

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage


def from_config(config_file: str,
                global_configs: Optional[List[str]] = None,
                tunables: Optional[List[str]] = None,
                **kwargs: Any) -> Storage:
    """
    Create a new storage object from JSON5 config file.

    Parameters
    ----------
    config_file : str
        JSON5 config file to load.
    global_configs : Optional[List[str]]
        An optional list of config files with global parameters.
    tunables : Optional[List[str]]
        An optional list of files containing JSON5 metadata of the tunables.
    kwargs : dict
        Additional configuration parameters.

    Returns
    -------
    storage : Storage
        A new storage object.
    """
    config_path: List[str] = kwargs.get("config_path", [])
    config_loader = ConfigPersistenceService({"config_path": config_path})
    global_config = {}
    for fname in (global_configs or []):
        config = config_loader.load_config(fname, ConfigSchema.GLOBALS)
        global_config.update(config)
        config_path += config.get("config_path", [])
        config_loader = ConfigPersistenceService({"config_path": config_path})
    global_config.update(kwargs)

    # pylint: disable=protected-access
    tunable_groups = config_loader._load_tunables(tunables or [], TunableGroups())
    class_config = config_loader.load_config(config_file, ConfigSchema.STORAGE)
    assert isinstance(class_config, Dict)

    ret = config_loader.build_generic(
        base_cls=Storage,  # type: ignore[type-abstract]
        tunables=tunable_groups,
        service=config_loader,
        config=class_config,
        global_config=global_config
    )
    assert isinstance(ret, Storage)
    return ret
