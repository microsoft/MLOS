#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Factory method to create a new :py:class:`.Storage` instance from a
:py:attr:`~mlos_bench.config.schemas.config_schemas.ConfigSchema.STORAGE` type json
config.

See Also
--------
mlos_bench.storage : For example usage.
"""

from typing import Any

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.storage.base_storage import Storage


def from_config(
    config: str,
    global_configs: list[str] | None = None,
    **kwargs: Any,
) -> Storage:
    """
    Create a new storage object from JSON5 config file.

    Parameters
    ----------
    config : str
        JSON5 config file or string to load.
    global_configs : Optional[list[str]]
        An optional list of config files with global parameters.
    kwargs : dict
        Additional configuration parameters.

    Returns
    -------
    storage : Storage
        A new storage object.
    """
    config_path: list[str] = kwargs.get("config_path", [])
    config_loader = ConfigPersistenceService({"config_path": config_path})
    global_config = {}
    for fname in global_configs or []:
        gconfig = config_loader.load_config(fname, ConfigSchema.GLOBALS)
        global_config.update(gconfig)
        config_path += gconfig.get("config_path", [])
        config_loader = ConfigPersistenceService({"config_path": config_path})
    global_config.update(kwargs)

    class_config = config_loader.load_config(config, ConfigSchema.STORAGE)
    assert isinstance(class_config, dict)

    ret = config_loader.build_storage(
        service=config_loader,
        config=class_config,
        global_config=global_config,
    )
    assert isinstance(ret, Storage)
    return ret
