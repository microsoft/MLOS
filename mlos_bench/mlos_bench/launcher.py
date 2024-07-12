#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A helper class to load the configuration files, parse the command line parameters, and
instantiate the main components of mlos_bench system.

It is used in `mlos_bench.run` module to run the benchmark/optimizer from the
command line.
"""

import argparse
import logging
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.dict_templater import DictTemplater
from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.optimizers.one_shot_optimizer import OneShotOptimizer
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.services.base_service import Service
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.services.types.config_loader_type import SupportsConfigLoading
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import try_parse_val

_LOG_LEVEL = logging.INFO
_LOG_FORMAT = "%(asctime)s %(filename)s:%(lineno)d %(funcName)s %(levelname)s %(message)s"
logging.basicConfig(level=_LOG_LEVEL, format=_LOG_FORMAT)

_LOG = logging.getLogger(__name__)


class Launcher:
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Command line launcher for mlos_bench and mlos_core."""

    def __init__(self, description: str, long_text: str = "", argv: Optional[List[str]] = None):
        # pylint: disable=too-many-statements
        _LOG.info("Launch: %s", description)
        epilog = """
            Additional --key=value pairs can be specified to augment or override
            values listed in --globals.
            Other required_args values can also be pulled from shell environment
            variables.

            For additional details, please see the website or the README.md files in
            the source tree:
            <https://github.com/microsoft/MLOS/tree/main/mlos_bench/>
            """
        parser = argparse.ArgumentParser(description=f"{description} : {long_text}", epilog=epilog)
        (args, args_rest) = self._parse_args(parser, argv)

        # Bootstrap config loader: command line takes priority.
        config_path = args.config_path or []
        self._config_loader = ConfigPersistenceService({"config_path": config_path})
        if args.config:
            config = self._config_loader.load_config(args.config, ConfigSchema.CLI)
            assert isinstance(config, Dict)
            # Merge the args paths for the config loader with the paths from JSON file.
            config_path += config.get("config_path", [])
            self._config_loader = ConfigPersistenceService({"config_path": config_path})
        else:
            config = {}

        log_level = args.log_level or config.get("log_level", _LOG_LEVEL)
        try:
            log_level = int(log_level)
        except ValueError:
            # failed to parse as an int - leave it as a string and let logging
            # module handle whether it's an appropriate log name or not
            log_level = logging.getLevelName(log_level)
        logging.root.setLevel(log_level)
        log_file = args.log_file or config.get("log_file")
        if log_file:
            log_handler = logging.FileHandler(log_file)
            log_handler.setLevel(log_level)
            log_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
            logging.root.addHandler(log_handler)

        self._parent_service: Service = LocalExecService(parent=self._config_loader)

        self.global_config = self._load_config(
            config.get("globals", []) + (args.globals or []),
            (args.config_path or []) + config.get("config_path", []),
            args_rest,
            {key: val for (key, val) in config.items() if key not in vars(args)},
        )
        # experiment_id is generally taken from --globals files, but we also allow
        # overriding it on the CLI.
        # It's useful to keep it there explicitly mostly for the --help output.
        if args.experiment_id:
            self.global_config["experiment_id"] = args.experiment_id
        # trial_config_repeat_count is a scheduler property but it's convenient to
        # set it via command line
        if args.trial_config_repeat_count:
            self.global_config["trial_config_repeat_count"] = args.trial_config_repeat_count
        # Ensure that the trial_id is present since it gets used by some other
        # configs but is typically controlled by the run optimize loop.
        self.global_config.setdefault("trial_id", 1)

        self.global_config = DictTemplater(self.global_config).expand_vars(use_os_env=True)
        assert isinstance(self.global_config, dict)

        # --service cli args should override the config file values.
        service_files: List[str] = config.get("services", []) + (args.service or [])
        assert isinstance(self._parent_service, SupportsConfigLoading)
        self._parent_service = self._parent_service.load_services(
            service_files,
            self.global_config,
            self._parent_service,
        )

        env_path = args.environment or config.get("environment")
        if not env_path:
            _LOG.error("No environment config specified.")
            parser.error(
                "At least the Environment config must be specified."
                + " Run `mlos_bench --help` and consult `README.md` for more info."
            )
        self.root_env_config = self._config_loader.resolve_path(env_path)

        self.environment: Environment = self._config_loader.load_environment(
            self.root_env_config, TunableGroups(), self.global_config, service=self._parent_service
        )
        _LOG.info("Init environment: %s", self.environment)

        # NOTE: Init tunable values *after* the Environment, but *before* the Optimizer
        self.tunables = self._init_tunable_values(
            args.random_init or config.get("random_init", False),
            config.get("random_seed") if args.random_seed is None else args.random_seed,
            config.get("tunable_values", []) + (args.tunable_values or []),
        )
        _LOG.info("Init tunables: %s", self.tunables)

        self.optimizer = self._load_optimizer(args.optimizer or config.get("optimizer"))
        _LOG.info("Init optimizer: %s", self.optimizer)

        self.storage = self._load_storage(args.storage or config.get("storage"))
        _LOG.info("Init storage: %s", self.storage)

        self.teardown: bool = (
            bool(args.teardown)
            if args.teardown is not None
            else bool(config.get("teardown", True))
        )
        self.scheduler = self._load_scheduler(args.scheduler or config.get("scheduler"))
        _LOG.info("Init scheduler: %s", self.scheduler)

    @property
    def config_loader(self) -> ConfigPersistenceService:
        """Get the config loader service."""
        return self._config_loader

    @property
    def service(self) -> Service:
        """Get the parent service."""
        return self._parent_service

    @staticmethod
    def _parse_args(
        parser: argparse.ArgumentParser,
        argv: Optional[List[str]],
    ) -> Tuple[argparse.Namespace, List[str]]:
        """Parse the command line arguments."""
        parser.add_argument(
            "--config",
            required=False,
            help="Main JSON5 configuration file. Its keys are the same as the"
            + " command line options and can be overridden by the latter.\n"
            + "\n"
            + " See the `mlos_bench/config/` tree at https://github.com/microsoft/MLOS/ "
            + " for additional config examples for this and other arguments.",
        )

        parser.add_argument(
            "--log_file",
            "--log-file",
            required=False,
            help="Path to the log file. Use stdout if omitted.",
        )

        parser.add_argument(
            "--log_level",
            "--log-level",
            required=False,
            type=str,
            help=f"Logging level. Default is {logging.getLevelName(_LOG_LEVEL)}."
            + " Set to DEBUG for debug, WARNING for warnings only.",
        )

        parser.add_argument(
            "--config_path",
            "--config-path",
            "--config-paths",
            "--config_paths",
            nargs="+",
            action="extend",
            required=False,
            help="One or more locations of JSON config files.",
        )

        parser.add_argument(
            "--service",
            "--services",
            nargs="+",
            action="extend",
            required=False,
            help=(
                "Path to JSON file with the configuration "
                "of the service(s) for environment(s) to use."
            ),
        )

        parser.add_argument(
            "--environment",
            required=False,
            help="Path to JSON file with the configuration of the benchmarking environment(s).",
        )

        parser.add_argument(
            "--optimizer",
            required=False,
            help="Path to the optimizer configuration file. If omitted, run"
            + " a single trial with default (or specified in --tunable_values).",
        )

        parser.add_argument(
            "--trial_config_repeat_count",
            "--trial-config-repeat-count",
            required=False,
            type=int,
            help=(
                "Number of times to repeat each config. "
                "Default is 1 trial per config, though more may be advised."
            ),
        )

        parser.add_argument(
            "--scheduler",
            required=False,
            help="Path to the scheduler configuration file. By default, use"
            + " a single worker synchronous scheduler.",
        )

        parser.add_argument(
            "--storage",
            required=False,
            help="Path to the storage configuration file."
            + " If omitted, use the ephemeral in-memory SQL storage.",
        )

        parser.add_argument(
            "--random_init",
            "--random-init",
            required=False,
            default=False,
            dest="random_init",
            action="store_true",
            help="Initialize tunables with random values. (Before applying --tunable_values).",
        )

        parser.add_argument(
            "--random_seed",
            "--random-seed",
            required=False,
            type=int,
            help="Seed to use with --random_init",
        )

        parser.add_argument(
            "--tunable_values",
            "--tunable-values",
            nargs="+",
            action="extend",
            required=False,
            help="Path to one or more JSON files that contain values of the tunable"
            + " parameters. This can be used for a single trial (when no --optimizer"
            + " is specified) or as default values for the first run in optimization.",
        )

        parser.add_argument(
            "--globals",
            nargs="+",
            action="extend",
            required=False,
            help="Path to one or more JSON files that contain additional"
            + " [private] parameters of the benchmarking environment.",
        )

        parser.add_argument(
            "--no_teardown",
            "--no-teardown",
            required=False,
            default=None,
            dest="teardown",
            action="store_false",
            help="Disable teardown of the environment after the benchmark.",
        )

        parser.add_argument(
            "--experiment_id",
            "--experiment-id",
            required=False,
            default=None,
            help="""
                Experiment ID to use for the benchmark.
                If omitted, the value from the --cli config or --globals is used.

                This is used to store and reload trial results from the storage.
                NOTE: It is **important** to change this value when incompatible
                changes are made to config files, scripts, versions, etc.
                This is left as a manual operation as detection of what is
                "incompatible" is not easily automatable across systems.
                """,
        )

        # By default we use the command line arguments, but allow the caller to
        # provide some explicitly for testing purposes.
        if argv is None:
            argv = sys.argv[1:].copy()
        (args, args_rest) = parser.parse_known_args(argv)

        return (args, args_rest)

    @staticmethod
    def _try_parse_extra_args(cmdline: Iterable[str]) -> Dict[str, TunableValue]:
        """Helper function to parse global key/value pairs from the command line."""
        _LOG.debug("Extra args: %s", cmdline)

        config: Dict[str, TunableValue] = {}
        key = None
        for elem in cmdline:
            if elem.startswith("--"):
                if key is not None:
                    raise ValueError("Command line argument has no value: " + key)
                key = elem[2:]
                kv_split = key.split("=", 1)
                if len(kv_split) == 2:
                    config[kv_split[0].strip()] = try_parse_val(kv_split[1])
                    key = None
            else:
                if key is None:
                    raise ValueError("Command line argument has no key: " + elem)
                config[key.strip()] = try_parse_val(elem)
                key = None

        if key is not None:
            # Handles missing trailing elem from last --key arg.
            raise ValueError("Command line argument has no value: " + key)

        _LOG.debug("Parsed config: %s", config)
        return config

    def _load_config(
        self,
        args_globals: Iterable[str],
        config_path: Iterable[str],
        args_rest: Iterable[str],
        global_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Get key/value pairs of the global configuration parameters from the specified
        config files (if any) and command line arguments.
        """
        for config_file in args_globals or []:
            conf = self._config_loader.load_config(config_file, ConfigSchema.GLOBALS)
            assert isinstance(conf, dict)
            global_config.update(conf)
        global_config.update(Launcher._try_parse_extra_args(args_rest))
        if config_path:
            global_config["config_path"] = config_path
        return global_config

    def _init_tunable_values(
        self,
        random_init: bool,
        seed: Optional[int],
        args_tunables: Optional[str],
    ) -> TunableGroups:
        """Initialize the tunables and load key/value pairs of the tunable values from
        given JSON files, if specified.
        """
        tunables = self.environment.tunable_params
        _LOG.debug("Init tunables: default = %s", tunables)

        if random_init:
            tunables = MockOptimizer(
                tunables=tunables,
                service=None,
                config={"start_with_defaults": False, "seed": seed},
            ).suggest()
            _LOG.debug("Init tunables: random = %s", tunables)

        if args_tunables is not None:
            for data_file in args_tunables:
                values = self._config_loader.load_config(data_file, ConfigSchema.TUNABLE_VALUES)
                assert isinstance(values, Dict)
                tunables.assign(values)
                _LOG.debug("Init tunables: load %s = %s", data_file, tunables)

        return tunables

    def _load_optimizer(self, args_optimizer: Optional[str]) -> Optimizer:
        """
        Instantiate the Optimizer object from JSON config file, if specified in the
        --optimizer command line option.

        If config file not specified, create a one-shot optimizer to run a single
        benchmark trial.
        """
        if args_optimizer is None:
            # global_config may contain additional properties, so we need to
            # strip those out before instantiating the basic oneshot optimizer.
            config = {
                key: val
                for key, val in self.global_config.items()
                if key in OneShotOptimizer.BASE_SUPPORTED_CONFIG_PROPS
            }
            return OneShotOptimizer(self.tunables, config=config, service=self._parent_service)
        class_config = self._config_loader.load_config(args_optimizer, ConfigSchema.OPTIMIZER)
        assert isinstance(class_config, Dict)
        optimizer = self._config_loader.build_optimizer(
            tunables=self.tunables,
            service=self._parent_service,
            config=class_config,
            global_config=self.global_config,
        )
        return optimizer

    def _load_storage(self, args_storage: Optional[str]) -> Storage:
        """
        Instantiate the Storage object from JSON file provided in the --storage command
        line parameter.

        If omitted, create an ephemeral in-memory SQL storage instead.
        """
        if args_storage is None:
            # pylint: disable=import-outside-toplevel
            from mlos_bench.storage.sql.storage import SqlStorage

            return SqlStorage(
                service=self._parent_service,
                config={
                    "drivername": "sqlite",
                    "database": ":memory:",
                    "lazy_schema_create": True,
                },
            )
        class_config = self._config_loader.load_config(args_storage, ConfigSchema.STORAGE)
        assert isinstance(class_config, Dict)
        storage = self._config_loader.build_storage(
            service=self._parent_service,
            config=class_config,
            global_config=self.global_config,
        )
        return storage

    def _load_scheduler(self, args_scheduler: Optional[str]) -> Scheduler:
        """
        Instantiate the Scheduler object from JSON file provided in the --scheduler
        command line parameter.

        Create a simple synchronous single-threaded scheduler if omitted.
        """
        # Set `teardown` for scheduler only to prevent conflicts with other configs.
        global_config = self.global_config.copy()
        global_config.setdefault("teardown", self.teardown)
        if args_scheduler is None:
            # pylint: disable=import-outside-toplevel
            from mlos_bench.schedulers.sync_scheduler import SyncScheduler

            return SyncScheduler(
                # All config values can be overridden from global config
                config={
                    "experiment_id": "UNDEFINED - override from global config",
                    "trial_id": 0,
                    "config_id": -1,
                    "trial_config_repeat_count": 1,
                    "teardown": self.teardown,
                },
                global_config=self.global_config,
                environment=self.environment,
                optimizer=self.optimizer,
                storage=self.storage,
                root_env_config=self.root_env_config,
            )
        class_config = self._config_loader.load_config(args_scheduler, ConfigSchema.SCHEDULER)
        assert isinstance(class_config, Dict)
        return self._config_loader.build_scheduler(
            config=class_config,
            global_config=self.global_config,
            environment=self.environment,
            optimizer=self.optimizer,
            storage=self.storage,
            root_env_config=self.root_env_config,
        )
