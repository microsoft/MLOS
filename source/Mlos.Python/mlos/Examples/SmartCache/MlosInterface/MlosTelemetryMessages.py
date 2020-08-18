#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
""" Types of all telemetry messages that this component can emit.

"""
from collections import namedtuple

SmartCacheGet = namedtuple("SmartCacheGet", ['key', 'was_hit'])
SmartCachePush = namedtuple("SmartCachePush", ['key'])
SmartCacheEvict = namedtuple("SmartCacheEvict", ['key'])
