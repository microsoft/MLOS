"""
Base class for the service mix-ins.
"""

import json
import logging
import importlib

_LOG = logging.getLogger(__name__)


class Service:
    """
    An abstract base of all environment services.
    """

    @staticmethod
    def from_config(config):
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with two mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.

        Returns
        -------
        svc : Service
            An instance of the `Service` class initialized with `config`.
        """
        svc_class = config["class"]
        svc_config = config["config"]
        _LOG.debug("Creating service: %s", svc_class)
        service = Service.new(svc_class, svc_config)
        _LOG.info("Created service: %s", service)
        return service

    @staticmethod
    def from_config_list(config_list, parent=None):
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config_list : a list of dict
            A list where each element is a dictionary with 2 mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        parent: Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        svc : Service
            An instance of the `Service` class that is a combination of all
            services from the list plus the parent mix-in.
        """
        service = Service()
        if parent:
            service.register(parent.export())
        for config in config_list:
            service.register(Service.from_config(config).export())
        _LOG.info("Created mix-in service: %s", service.export())
        return service

    @classmethod
    def new(cls, class_name, config):
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

    def __init__(self, config=None):
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

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Config:\n%s", json.dumps(self.config, indent=2))

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

    def export(self):
        """
        Return a dictionary of functions available in this service.

        Returns
        -------
        services : dict
            A dictionary of string -> function pairs.
        """
        return self._services
