"""
Interfaces and wrapper classes for optimizers to be used in Autotune.
"""

import logging

from mlos_bench.util import prepare_class_load
from mlos_bench.environment.tunable import TunableGroups

from mlos_bench.optimizer.base_optimizer import Optimizer
from mlos_bench.optimizer.mock_optimizer import MockOptimizer
from mlos_bench.optimizer.mlos_core_optimizer import MlosCoreOptimizer

_LOG = logging.getLogger(__name__)

__all__ = [
    'Optimizer',
    'MockOptimizer',
    'MlosCoreOptimizer',
]


def load_optimizer(tunables: TunableGroups,
                   config: dict, global_config: dict = None) -> Optimizer:
    """
    Instantiate the Optimizer shim from the configuration.

    Parameters
    ----------
    tunables : TunableGroups
        Tunable parameters of the environment.
    config : dict
        Configuration of the optimizer.
    global_config : dict
        Global configuration parameters (optional).

    Returns
    -------
    opt : Optimizer
        A new Optimizer instance.
    """
    (class_name, opt_config) = prepare_class_load(config, global_config)
    opt = Optimizer.new(class_name, tunables, opt_config)
    _LOG.info("Created optimizer: %s", opt)
    return opt
