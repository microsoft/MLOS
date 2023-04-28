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

from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.storage.base_storage import Storage
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.util import BaseTypes

_LOG_LEVEL = logging.INFO
_LOG_FORMAT = '%(asctime)s %(filename)s:%(lineno)d %(funcName)s %(levelname)s %(message)s'
logging.basicConfig(level=_LOG_LEVEL, format=_LOG_FORMAT)

_LOG = logging.getLogger(__name__)


class Launcher:
    """
    Common parts of the mlos_bench command line launchers.
    """

    def __init__(self, description: str):

        _LOG.info("Launch: %s", description)

        self._config_loader: ConfigPersistenceService
        self._env_config_file: str
        self._global_config: Dict[str, Any] = {}
        self._parser = argparse.ArgumentParser(description=description)

        self._parser.add_argument(
            '--log', required=False, dest='log_file',
            help='Path to the log file. Use stdout if omitted.')

        self._parser.add_argument(
            '--log-level', required=False, type=int, default=_LOG_LEVEL,
            help=f'Logging level. Default is {_LOG_LEVEL} ({logging.getLevelName(_LOG_LEVEL)}).' +
                 f' Set to {logging.DEBUG} for debug, {logging.WARNING} for warnings only.')

        self._parser.add_argument(
            '--environment', required=True,
            help='Path to JSON file with the configuration of the benchmarking environment.')

        self._parser.add_argument(
            '--config-path', nargs="+", required=False,
            help='One or more locations of JSON config files.')

        self._parser.add_argument(
            '--globals', nargs="+", required=False,
            help='Path to one or more JSON files that contain additional' +
                 ' [private] parameters of the benchmarking environment.')

        self._parser.add_argument(
            '--no-teardown', required=False, default=True,
            dest='teardown', action='store_false',
            help='Disable teardown of the environment after the benchmark.')

    @property
    def parser(self) -> argparse.ArgumentParser:
        """
        Get the command line parser (so we can add more arguments to it).
        """
        return self._parser

    @property
    def root_env_config(self) -> str:
        """
        Get the global parameters that can override the values in the config snippets.
        """
        assert self._env_config_file, "Call after invoking .parse_args()"
        return self._env_config_file

    @property
    def global_config(self) -> Dict[str, Any]:
        """
        Get the global parameters that can override the values in the config snippets.
        """
        return self._global_config

    def parse_args(self) -> argparse.Namespace:
        """
        Parse command line arguments and load global config parameters.
        """
        (args, args_rest) = self._parser.parse_known_args()

        logging.root.setLevel(args.log_level)
        if args.log_file:
            log_handler = logging.FileHandler(args.log_file)
            log_handler.setLevel(args.log_level)
            log_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
            logging.root.addHandler(log_handler)

        self._config_loader = ConfigPersistenceService({"config_path": args.config_path})
        self._env_config_file = self._config_loader.resolve_path(args.environment)

        if args.globals is not None:
            for config_file in args.globals:
                conf = self._config_loader.load_config(config_file)
                assert isinstance(conf, dict)
                self._global_config.update(conf)

        self._global_config.update(Launcher._try_parse_extra_args(args_rest))
        if args.config_path:
            self._global_config["config_path"] = args.config_path

        return args

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

    def load_config(self, json_file_name: str) -> Dict[str, Any]:
        """
        Load JSON config file. Use path relative to `config_path` if required.
        """
        assert self._config_loader is not None, "Call after invoking .parse_args()"
        conf = self._config_loader.load_config(json_file_name)
        assert isinstance(conf, dict)
        return conf

    def load_environment(self) -> Environment:
        """
        Create a new benchmarking environment from the configs and command line parameters.
        Inject the persistence service so that the environment can load other configs.
        """
        assert self._config_loader is not None, "Call after invoking .parse_args()"
        return self._config_loader.load_environment(
            self._env_config_file, self._global_config,
            service=LocalExecService(parent=self._config_loader))

    def load_optimizer(self, env: Environment, json_file_name: str) -> Optimizer:
        """
        Create a new instance of the Optimizer from JSON configuration.
        """
        opt = self._load(env, Optimizer, json_file_name)
        assert isinstance(opt, Optimizer)
        return opt

    def load_storage(self, env: Environment, json_file_name: str) -> Storage:
        """
        Create a new instance of the Storage from JSON configuration.
        """
        storage = self._load(env, Storage, json_file_name)
        assert isinstance(storage, Storage)
        return storage

    def _load(self, env: Environment, cls: type, json_file_name: str) -> BaseTypes:
        """
        Create a new instance of class `cls` from JSON configuration.
        """
        assert self._config_loader is not None, "Call after invoking .parse_args()"
        return self._config_loader.build_generic(
            base_cls=cls,
            tunables=env.tunable_params(),
            service=self._config_loader,
            config=self.load_config(json_file_name),
            global_config=self.global_config
        )
