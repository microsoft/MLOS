#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A helper class to load the configuration files, parse the command line parameters,
and instantiate the main components of mlos_bench system.

It is used in `mlos_bench.run` module to run the benchmark/optimizer from the
command line.
"""

import logging
import argparse
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.util import BaseTypeVar

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.environments.base_environment import Environment

from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.one_shot_optimizer import OneShotOptimizer

from mlos_bench.storage.base_storage import Storage

from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.services.config_persistence import ConfigPersistenceService


_LOG_LEVEL = logging.INFO
_LOG_FORMAT = '%(asctime)s %(filename)s:%(lineno)d %(funcName)s %(levelname)s %(message)s'
logging.basicConfig(level=_LOG_LEVEL, format=_LOG_FORMAT)

_LOG = logging.getLogger(__name__)


class Launcher:
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """
    Command line launcher for mlos_bench and mlos_core.
    """

    def __init__(self, description: str):

        _LOG.info("Launch: %s", description)
        parser = argparse.ArgumentParser(description=description)
        (args, args_rest) = self._parse_args(parser)

        # Bootstrap config loader: command line takes priority.
        self._config_loader = ConfigPersistenceService({"config_path": args.config_path or []})
        if args.config:
            config = self._config_loader.load_config(args.config, ConfigSchema.CLI)
            assert isinstance(config, Dict)
            config_path = config.get("config_path", [])
            if config_path and not args.config_path:
                # Reset the config loader with the paths from JSON file.
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

        self._parent_service = LocalExecService(parent=self._config_loader)

        self.global_config = self._load_config(
            args.globals or config.get("globals", []),
            args.config_path or config.get("config_path", []),
            args_rest,
            {key: val for (key, val) in config.items() if key not in vars(args)},
        )

        env_path = args.environment or config.get("environment")
        if not env_path:
            _LOG.error("No environment config specified.")
            parser.error("At least the Environment config must be specified." +
                         " Run `mlos_bench --help` and consult `README.md` for more info.")
        self.root_env_config = self._config_loader.resolve_path(env_path)

        tunable_groups = TunableGroups()    # base tunable groups that all others get build on
        self.environment: Environment = self._config_loader.load_environment(
            self.root_env_config, tunable_groups, self.global_config, service=self._parent_service)

        # NOTE: Load the tunable values *before* the optimizer
        self.tunables = self._load_tunable_values(args.tunable_values or config.get("tunable_values", []))
        self.optimizer = self._load_optimizer(args.optimizer or config.get("optimizer"))
        self.storage = self._load_storage(args.storage or config.get("storage"))

        self.teardown = args.teardown or config.get("teardown", True)

    @staticmethod
    def _parse_args(parser: argparse.ArgumentParser) -> Tuple[argparse.Namespace, List[str]]:
        """
        Parse the command line arguments.
        """
        parser.add_argument(
            '--config', required=False,
            help='Main JSON5 configuration file. Its keys are the same as the' +
                 ' command line options and can be overridden by the latter.')

        parser.add_argument(
            '--log_file', required=False,
            help='Path to the log file. Use stdout if omitted.')

        parser.add_argument(
            '--log_level', required=False, type=str,
            help=f'Logging level. Default is {logging.getLevelName(_LOG_LEVEL)}.' +
                 ' Set to DEBUG for debug, WARNING for warnings only.')

        parser.add_argument(
            '--config_path', nargs="+", required=False,
            help='One or more locations of JSON config files.')

        parser.add_argument(
            '--environment', required=False,
            help='Path to JSON file with the configuration of the benchmarking environment.')

        parser.add_argument(
            '--optimizer', required=False,
            help='Path to the optimizer configuration file. If omitted, run' +
                 ' a single trial with default (or specified in --tunable_values).')

        parser.add_argument(
            '--storage', required=False,
            help='Path to the storage configuration file.' +
                 ' If omitted, use the ephemeral in-memory SQL storage.')

        parser.add_argument(
            '--tunable_values', nargs="+", required=False,
            help='Path to one or more JSON files that contain values of the tunable' +
                 ' parameters. This can be used for a single trial (when no --optimizer' +
                 ' is specified) or as default values for the first run in optimization.')

        parser.add_argument(
            '--globals', nargs="+", required=False,
            help='Path to one or more JSON files that contain additional' +
                 ' [private] parameters of the benchmarking environment.')

        parser.add_argument(
            '--no_teardown', required=False, default=None,
            dest='teardown', action='store_false',
            help='Disable teardown of the environment after the benchmark.')

        return parser.parse_known_args()

    @staticmethod
    def _try_parse_extra_args(cmdline: Iterable[str]) -> Dict[str, str]:
        """
        Helper function to parse global key/value pairs from the command line.
        """
        _LOG.debug("Extra args: %s", cmdline)

        config = {}
        key = None
        for elem in cmdline:
            if elem.startswith("--"):
                if key is not None:
                    raise ValueError("Command line argument has no value: " + key)
                key = elem[2:]
                kv_split = key.split("=", 1)
                if len(kv_split) == 2:
                    config[kv_split[0].strip()] = kv_split[1]
                    key = None
            else:
                if key is None:
                    raise ValueError("Command line argument has no key: " + elem)
                config[key.strip()] = elem
                key = None

        if key is not None:
            raise ValueError("Command line argument has no value: " + key)

        _LOG.debug("Parsed config: %s", config)
        return config

    def _load_config(self,
                     args_globals: Iterable[str],
                     config_path: Iterable[str],
                     args_rest: Iterable[str],
                     global_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get key/value pairs of the global configuration parameters
        from the specified config files (if any) and command line arguments.
        """
        for config_file in (args_globals or []):
            conf = self._config_loader.load_config(config_file, ConfigSchema.GLOBALS)
            assert isinstance(conf, dict)
            global_config.update(conf)
        global_config.update(Launcher._try_parse_extra_args(args_rest))
        if config_path:
            global_config["config_path"] = config_path
        return global_config

    def _load_tunable_values(self, args_tunables: Optional[str]) -> TunableGroups:
        """
        Load key/value pairs of the tunable values from given JSON files, if any.
        """
        tunables = self.environment.tunable_params
        if args_tunables is not None:
            for data_file in args_tunables:
                values = self._config_loader.load_config(data_file, ConfigSchema.TUNABLE_VALUES)
                assert isinstance(values, Dict)
                tunables.assign(values)
        return tunables

    def _load_optimizer(self, args_optimizer: Optional[str]) -> Optimizer:
        """
        Instantiate the Optimizer object from JSON config file, if specified
        in the --optimizer command line option. If config file not specified,
        create a one-shot optimizer to run a single benchmark trial.
        """
        if args_optimizer is None:
            return OneShotOptimizer(
                self.tunables, self._parent_service, self.global_config)
        optimizer = self._load(Optimizer, args_optimizer, ConfigSchema.OPTIMIZER)   # type: ignore[type-abstract]
        return optimizer

    def _load_storage(self, args_storage: Optional[str]) -> Storage:
        """
        Instantiate the Storage object from JSON file provided in the --storage
        command line parameter. If omitted, create an ephemeral in-memory SQL
        storage instead.
        """
        if args_storage is None:
            # pylint: disable=import-outside-toplevel
            from mlos_bench.storage.sql.storage import SqlStorage
            return SqlStorage(self.tunables, self._parent_service,
                              {"drivername": "sqlite", "database": ":memory:"})
        storage = self._load(Storage, args_storage, ConfigSchema.STORAGE)   # type: ignore[type-abstract]
        return storage

    def _load(self, cls: Type[BaseTypeVar], json_file_name: str, schema_type: Optional[ConfigSchema]) -> BaseTypeVar:
        """
        Create a new instance of class `cls` from JSON configuration.

        Note: For abstract types, mypy will complain at the call site.
        Use "# type: ignore[type-abstract]" to suppress the warning.
        See Also: https://github.com/python/mypy/issues/4717
        """
        class_config = self._config_loader.load_config(json_file_name, schema_type)
        assert isinstance(class_config, Dict)
        ret = self._config_loader.build_generic(
            base_cls=cls,
            tunables=self.tunables,
            service=self._parent_service,
            config=class_config,
            global_config=self.global_config
        )
        assert isinstance(ret, cls)
        return ret
