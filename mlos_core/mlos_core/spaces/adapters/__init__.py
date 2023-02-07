"""
Basic initializer module for the mlos_core space adapters.
"""

from enum import Enum
from mlos_core.spaces.adapters.llamatune import LlamaTuneAdapter


__all__ = [
    'LlamaTuneAdapter',
]


class SpaceAdapterType(Enum):
    """Enumerate supported MlosCore space adapters."""

    LLAMATUNE = LlamaTuneAdapter
    """An instance of LlamaTuneAdapter class will be used"""
