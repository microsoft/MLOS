#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper functions to launch the benchmark and the optimizer from the command line.
"""

import logging
import argparse

from typing import Any, Dict, Iterable

from mlos_bench.optimizer.base_optimizer import Optimizer
from mlos_bench.optimizer.one_shot_optimizer import OneShotOptimizer

from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.storage import SqlStorage

from mlos_bench.service.local.local_exec import LocalExecService
from mlos_bench.service.config_persistence import ConfigPersistenceService

from mlos_bench.util import BaseTypes

_LOG_LEVEL = logging.INFO
_LOG_FORMAT = '%(asctime)s %(filename)s:%(lineno)d %(funcName)s %(levelname)s %(message)s'
logging.basicConfig(level=_LOG_LEVEL, format=_LOG_FORMAT)

_LOG = logging.getLogger(__name__)


class Launcher:
    """
    Command line launcher for mlos_bench and mlos_core.
    """

    def __init__(self, description: str):

        _LOG.info("Launch: %s", description)
        parser = argparse.ArgumentParser(description=description)

        parser.add_argument(
            '--log', required=False, dest='log_file',
            help='Path to the log file. Use stdout if omitted.')

        parser.add_argument(
            '--log-level', required=False, type=int, default=_LOG_LEVEL,
            help=f'Logging level. Default is {_LOG_LEVEL} ({logging.getLevelName(_LOG_LEVEL)}).' +
                 f' Set to {logging.DEBUG} for debug, {logging.WARNING} for warnings only.')

        parser.add_argument(
            '--config-path', nargs="+", required=False,
            help='One or more locations of JSON config files.')

        parser.add_argument(
            '--environment', required=True,
            help='Path to JSON file with the configuration of the benchmarking environment.')

        parser.add_argument(
            '--optimizer', required=False,
            help='Path to the optimizer configuration file. If omitted, run' +
                 ' a single trial with default (or specified in --tunables) values.')

        parser.add_argument(
            '--storage', required=False,
            help='Path to the storage configuration file.' +
                 ' If omitted, use the ephemeral in-memory SQL storage.')

        parser.add_argument(
            '--tunables', nargs="+", required=False,
            help='Path to one or more JSON files that contain values of the tunable' +
                 ' parameters. This can be used for a single trial (when no --optimizer' +
                 ' is specified) or as default values for the first run in optimization.')

        parser.add_argument(
            '--globals', nargs="+", required=False,
            help='Path to one or more JSON files that contain additional' +
                 ' [private] parameters of the benchmarking environment.')

        parser.add_argument(
            '--no-teardown', required=False, default=True,
            dest='teardown', action='store_false',
            help='Disable teardown of the environment after the benchmark.')

        (args, args_rest) = parser.parse_known_args()

        logging.root.setLevel(args.log_level)
        if args.log_file:
            log_handler = logging.FileHandler(args.log_file)
            log_handler.setLevel(args.log_level)
            log_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
            logging.root.addHandler(log_handler)

        self._config_loader = ConfigPersistenceService({"config_path": args.config_path})
        self._parent_service = LocalExecService(parent=self._config_loader)

        self.global_config: Dict[str, Any] = {}
        if args.globals is not None:
            for config_file in args.globals:
                conf = self._config_loader.load_config(config_file)
                assert isinstance(conf, dict)
                self.global_config.update(conf)

        self.global_config.update(Launcher._try_parse_extra_args(args_rest))
        if args.config_path:
            self.global_config["config_path"] = args.config_path

        self.root_env_config = self._config_loader.resolve_path(args.environment)
        self.environment = self._config_loader.load_environment(
            self.root_env_config, self.global_config, service=self._parent_service)

        self.teardown: bool = args.teardown

        self.tunables = self.environment.tunable_params()
        if args.tunables is not None:
            for data_file in args.tunables:
                values = self._config_loader.load_config(data_file)
                assert isinstance(values, Dict)
                self.tunables.assign(values)

        self.optimizer: Optimizer
        if args.optimizer is None:
            self.optimizer = OneShotOptimizer(
                self.tunables, self._parent_service, self.global_config)
        else:
            opt = self._load(Optimizer, args.optimizer)
            assert isinstance(opt, Optimizer)
            self.optimizer = opt

        self.storage: Storage
        if args.storage is None:
            self.storage = SqlStorage(
                self.tunables, self._parent_service, {
                    "drivername": "sqlite",
                    "database": ":memory:",
                    **self.global_config,
                })
        else:
            storage = self._load(Storage, args.storage)
            assert isinstance(storage, Storage)
            self.storage = storage

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

    def _load(self, cls: type, json_file_name: str) -> BaseTypes:
        """
        Create a new instance of class `cls` from JSON configuration.
        """
        class_config = self._config_loader.load_config(json_file_name)
        assert isinstance(class_config, Dict)
        return self._config_loader.build_generic(
            base_cls=cls,
            tunables=self.tunables,
            service=self._parent_service,
            config=class_config,
            global_config=self.global_config
        )
