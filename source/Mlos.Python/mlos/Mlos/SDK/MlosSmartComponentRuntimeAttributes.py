#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import namedtuple


def MlosSmartComponentRuntimeAttributes(smart_component_name, attribute_names):
    assert 'mlos_object_id' not in attribute_names
    attribute_names.append('component_id')
    smart_component_name += 'RuntimeAttributes'
    return namedtuple(smart_component_name, attribute_names)
