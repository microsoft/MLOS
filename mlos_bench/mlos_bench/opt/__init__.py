"""
Interfaces and wrapper classes for optimizers to be used in Autotune.
"""

from mlos_bench.opt.base_opt import Optimizer
from mlos_bench.opt.mock_opt import MockOptimizer

__all__ = [
    'Optimizer',
    'MockOptimizer',
]
