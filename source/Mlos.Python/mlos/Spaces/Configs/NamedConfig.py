#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import Point

class NamedConfig:
    """ A simple plain old Python object to keep a named config along with its description.

    """
    def __init__(self, name: str, config_point: Point, description: str):
        assert name is not None and len(name) > 0
        assert config_point is not None

        self.name = name
        self.config_point = config_point
        self.description = description

    def copy(self):
        return NamedConfig(name=self.name, config_point=self.config_point.copy(), description=self.description)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Name: {self.name}\n\nDescription: {self.description}\n\nConfig Values: {self.config_point.to_json(indent=2)}"
