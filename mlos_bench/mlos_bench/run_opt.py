#!/usr/bin/env python3
"""
OS Autotune main optimization loop.

See `--help` output for details.
"""

import json
import logging

from mlos_bench.launcher import Launcher
from mlos_bench.optimizer import Optimizer
from mlos_bench.environment import Status, Environment, TunableGroups

_LOG = logging.getLogger(__name__)


def _main():

    launcher = Launcher("OS Autotune optimizer")

    launcher.parser.add_argument(
        '--optimizer', required=True,
        help='Path to the optimizer configuration file.')

    launcher.parser.add_argument(
        '--no-teardown', required=False, default=False, action='store_true',
        help='Disable teardown of the environment after the optimization.')

    args = launcher.parse_args()

    config = launcher.global_config
    env = launcher.load_env()

    opt = _load_optimizer(
        env.tunable_params(), launcher.load_config(args.optimizer), config)

    result = _optimize(config["experimentId"], env, opt)
    _LOG.info("Final result: %s", result)

    if not args.no_teardown:
        env.teardown()


def _load_optimizer(tunables: TunableGroups, config: dict, global_config: dict) -> Optimizer:
    """
    Instantiate the Optimizer shim from the configuration.

    Parameters
    ----------
    tunables : TunableGroups
        Tunable parameters of the environment.
    config : dict
        Configuration of the optimizer.
    global_config : dict
        Global configuration parameters.

    Returns
    -------
    opt : Optimizer
        A new Optimizer instance.
    """
    class_name = config["class"]
    opt_config = config.setdefault("config", {})

    for key in set(opt_config).intersection(global_config or {}):
        opt_config[key] = global_config[key]

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Creating optimizer: %s with config:\n%s",
                   class_name, json.dumps(opt_config, indent=2))

    opt = Optimizer.new(class_name, tunables, opt_config)

    _LOG.info("Created optimizer: %s", opt)
    return opt


def _optimize(experiment_id: str, env: Environment, opt: Optimizer):
    """
    Main optimization loop.
    """
    _LOG.info("Experiment: %s Env: %s Optimizer: %s", experiment_id, env, opt)

    # Somehow connect to the persistence service using the global parameters
    db = None

    # Get records of (tunables, status, score) (?) from the previous runs
    # of the same experiment (or several experiments).
    # Q: How to restore the telemetry and specify the optimization target?
    (run_id, tunables_data) = db.restore(experiment_id)
    opt.update(tunables_data)
    # ...can do it more than once for multiple experiments

    opt_target = 'score'
    opt_direction = 'min'

    while opt.not_converged():

        run_id += 1
        tunables = opt.suggest()
        _LOG.info("%s:%d Suggestion: %s", experiment_id, run_id, tunables)

        with db.experiment(tunables, experiment_id, run_id) as exp:

            if not env.setup(tunables):  # pass experimentName and experimentId here
                _LOG.warning("Setup failed: %s :: %s", env, tunables)
                exp.update(Status.FAILED)
                opt.register(tunables, Status.FAILED)
                continue

            (status, value) = env.benchmark()  # Block and wait for the final result.
            # `value` is a DataFrame with one row and one or more benchmark results.
            exp.update(status, value)

            value = value.loc[0, opt_target] if status.is_succeeded else None

            _LOG.info("Result: %s = %s :: %s", tunables, status, value)
            opt.register(tunables, status, value)

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


if __name__ == "__main__":
    _main()
