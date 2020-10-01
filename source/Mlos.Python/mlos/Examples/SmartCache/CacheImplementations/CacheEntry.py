#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class CacheEntry:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return str(vars(self))
