#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Factory method to create a new Storage instance from configs."""

from typing import Any, Dict, List, Optional

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.storage.base_storage import Storage


def from_config(
    config_file: str,
    global_configs: Optional[List[str]] = None,
    **kwargs: Any,
) -> Storage:
    """
    Create a new storage object from JSON5 config file.

    Parameters
    ----------
    config_file : str
        JSON5 config file to load.
    global_configs : Optional[List[str]]
        An optional list of config files with global parameters.
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
    for fname in global_configs or []:
        config = config_loader.load_config(fname, ConfigSchema.GLOBALS)
        global_config.update(config)
        config_path += config.get("config_path", [])
        config_loader = ConfigPersistenceService({"config_path": config_path})
    global_config.update(kwargs)

    class_config = config_loader.load_config(config_file, ConfigSchema.STORAGE)
    assert isinstance(class_config, Dict)

    ret = config_loader.build_storage(
        service=config_loader,
        config=class_config,
        global_config=global_config,
    )
    assert isinstance(ret, Storage)
    return ret
