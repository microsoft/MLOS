#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import Dict

from mlos.Exceptions import PointOutOfDomainException
from mlos.Spaces import Hypergrid, Point
from mlos.Spaces.Configs.NamedConfig import NamedConfig

class ComponentConfigStore:
    """ A place for a component to keep its named configs and the Hypergrid describing its parameter space.

    Right now such functionality is spread across XYZConfig classes which presents the following problems:
        * Instances of these classes are mostly superfluous because they generally only wrap a Point() instance.
        * There is not really a good place to put a description of each parameter for users to discover it.
        * It's a pain to write and for most uses unnecessary since the Point instance has all the required information.

    """
    def __init__(self, parameter_space: Hypergrid, default: Point, description: str = None):

        assert isinstance(parameter_space, Hypergrid)
        assert default in parameter_space, f"{default} not in \n{parameter_space}"

        self.parameter_space = parameter_space
        self._default = default
        self.description = description

        self._named_configs: Dict[str, Point] = {'default': default}

        # Optionally each config can have a description stored in this dict:
        #   key: config name
        #   value: config description
        self._named_configs_descriptions: Dict[str, str] = {'default': 'default'}

    @property
    def default(self):
        return self._default.copy()

    def is_valid_config(self, config_point: Point):
        return config_point in self.parameter_space

    def add_config_by_name(self, config_point: Point, config_name: str, description: str = None) -> None:
        if config_point not in self.parameter_space:
            raise PointOutOfDomainException(f"The supplied point: {config_point.to_json(indent=2)} "
                                            f"does not belong to the components parameter space \n{self.parameter_space}")

        self._named_configs[config_name] = config_point
        self._named_configs_descriptions[config_name] = description

    def list_named_configs(self):
        return [
            NamedConfig(name=config_name, config_point=config_point, description=self._named_configs_descriptions[config_name])
            for config_name, config_point in self._named_configs.items()
        ]

    def get_config_by_name(self, name: str) -> str:
        # Throws a Key error if config not found, which is exactly what we want to throw.
        #
        return self._named_configs[name].copy()
