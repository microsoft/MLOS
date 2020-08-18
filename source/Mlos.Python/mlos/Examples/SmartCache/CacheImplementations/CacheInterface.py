#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod

class CacheInterface(ABC):
    """ An interface implemented by all cache implementations."""

    @abstractmethod
    def __init__(self):
        ...

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    @abstractmethod
    def __len__(self):
        raise NotImplementedError()

    @abstractmethod
    def __contains__(self, key):
        raise NotImplementedError()

    @abstractmethod
    def get(self, key):
        raise NotImplementedError()

    @abstractmethod
    def push(self, cache_entry):
        raise NotImplementedError()
