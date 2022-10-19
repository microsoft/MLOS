"""
Base class for the service mix-ins.
"""

import os
import json
import logging
import importlib

from typing import Callable, Dict

_LOG = logging.getLogger(__name__)


class Service:
    """
    An abstract base of all environment services.
    """

    @classmethod
    def new(cls, class_name: str, config: dict):
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        class_name: str
            FQN of a Python class to instantiate, e.g.,
            "mlos_bench.environment.azure.AzureVMService".
            Must be derived from the `Service` class.
        config : dict
            Free-format dictionary that contains the service configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.

        Returns
        -------
        svc : Service
            An instance of the `Service` class initialized with `config`.
        """
        # We need to import mlos_bench to make the factory methods
        # like `Service.new()` work.
        class_name_split = class_name.split(".")
        module_name = ".".join(class_name_split[:-1])
        class_id = class_name_split[-1]

        env_module = importlib.import_module(module_name)
        svc_class = getattr(env_module, class_id)
        _LOG.info("Instantiating: %s :: %s", class_name, svc_class)

        assert issubclass(svc_class, cls)
        return svc_class(config)

    def __init__(self, config: dict = None):
        """
        Create a new service with a given config.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the service configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.
        """
        self.config = config or {}
        self._services = {}
        self._config_dir = self.config.get("config_dir")

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Service config:\n%s", json.dumps(self.config, indent=2))

        self.register([
            self.get_config_path,
            self.load_config
        ])

    def get_config_path(self, path: str) -> str:
        """
        Prepend `_config_dir` to `path` if the latter is not absolute.
        If `_config_dir` is `None` or `path` is absolute, return `path` as is.

        Parameters
        ----------
        path : str
            Path to the input config file.

        Returns
        -------
        path : str
            An actual absolute path to the config.
        """
        if self._config_dir and not os.path.isabs(path):
            path = os.path.join(self._config_dir, path)
        return os.path.abspath(path)

    def load_config(self, json_file_name: str) -> dict:
        """
        Load JSON config file. Use path relative to `_config_dir` if required.
        This method is exported to be used as a service.

        Parameters
        ----------
        json_file_name : str
            Path to the input config file.

        Returns
        -------
        config : dict
            Free-format dictionary that contains the configuration.
        """
        json_file_name = self.get_config_path(json_file_name)
        _LOG.info("Load config: %s", json_file_name)
        with open(json_file_name, mode='r', encoding='utf-8') as fh_json:
            return json.load(fh_json)

    def register(self, services):
        """
        Register new mix-in services.

        Parameters
        ----------
        services : dict or list
            A dictionary of string -> function pairs.
        """
        if not isinstance(services, dict):
            services = {svc.__name__: svc for svc in services}
        self._services.update(services)
        self.__dict__.update(self._services)

    def export(self) -> Dict[str, Callable]:
        """
        Return a dictionary of functions available in this service.

        Returns
        -------
        services : dict
            A dictionary of string -> function pairs.
        """
        return self._services
