#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import namedtuple

from .CommunicationChannel import CommunicationChannel
from .ConfigurationManager import ConfigurationManager
from .RuntimeDecisionsManager import RuntimeDecisionsManager
from .SharedConfig import SharedConfig
from .SmartComponentManager import SmartComponentManager
from .TelemetryManager import TelemetryManager

RegisterSmartComponentMessage = namedtuple(
    'RegisterSmartComponentMessage', [
        'component_type_name',
        'component_runtime_attributes'
    ]
)

UnregisterSmartComponentMessage = namedtuple(
    'UnregisterSmartComponentMessage', [
        'component_type_name',
        'component_runtime_attributes'
    ]
)

__all__ = [
    "CommunicationChannel",
    "ConfigurationManager",
    "RegisterSmartComponentMessage",
    "RuntimeDecisionsManager",
    "SharedConfig",
    "SmartComponentManager",
    "TelemetryManager",
    "UnregisterSmartComponentMessage",
]
