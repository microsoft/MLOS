#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

from abc import ABCMeta

class DefaultConfigMeta(ABCMeta):
    # metaclass that allows class-level properties on a config
    @property
    def DEFAULT(cls):
        return cls._DEFAULT.copy()
