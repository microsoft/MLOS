#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
from typing import Iterator

from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer

class BayesianOptimizerStoreBase(ABC):
    """Defines the interface to all BayesianOptimizerStores.

    When exposing the BayesianOptimizer as a service any request handler processing a create/train/query request must be able to:
        1. Place an optimizer in the store so that all other handler threads/processes can see it - in case of create/train requests
        2. Retrieve an optimizer from the store, and either query it or re-train it.

    It's reasonable to assume that we will have several concrete implementations of this store:
        1. One in memory for fast tests etc - that's what we use now.
        2. One based on a SQL Server database
        3. One based on MLFlow maybe
        4. File system based one

    All such implementations must support a way to retrieve an optimizer and operate on it with an exclusive lock, or a reader-writer
    lock (for purely querying an optimizer).


    """

    @abstractmethod
    def exclusive_optimizer(self, optimizer_id) -> Iterator[BayesianOptimizer]:
        raise NotImplementedError
