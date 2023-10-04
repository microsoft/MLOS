#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Factory method to create a new Storage instance from configs.
"""

from typing import Optional, List, Dict

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage


def from_config(config_file: str,
                tunables_files: Optional[List[str]] = None,
                **kwargs: dict) -> Storage:
    """
    Create a new storage object from JSON5 config file.

    Parameters
    ----------
    config_file : str
        JSON5 config file to load.
    tunables_files : Optional[List[str]]
        An optional list of files containing JSON5 metadata of the tunables.
    kwargs : dict
        Additional configuration parameters.

    Returns
    -------
    storage : Storage
        A new storage object.
    """
    config_loader = ConfigPersistenceService(kwargs)
    class_config = config_loader.load_config(config_file, ConfigSchema.STORAGE)
    tunables = TunableGroups()
    for fname in (tunables_files or []):
        # pylint: disable=protected-access
        tunables = config_loader._load_tunables(fname, tunables)
    assert isinstance(class_config, Dict)
    ret = config_loader.build_generic(
        base_cls=Storage,  # type: ignore[type-abstract]
        tunables=tunables,
        service=config_loader,
        config=class_config,
        global_config=kwargs
    )
    assert isinstance(ret, Storage)
    return ret
