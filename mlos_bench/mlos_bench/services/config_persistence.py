#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Helper functions to load, instantiate, and serialize Python objects that encapsulate
a benchmark :py:class:`.Environment`, :py:mod:`~mlos_bench.tunables`,
:py:class:`.Service` functions, etc from JSON configuration files and strings.
"""

import logging
import os
from collections.abc import Callable, Iterable
from importlib.resources import files
from typing import TYPE_CHECKING, Any

import json5  # To read configs with comments and other JSON5 syntax features
from jsonschema import SchemaError, ValidationError

from mlos_bench.config.schemas.config_schemas import ConfigSchema
from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.config_loader_type import SupportsConfigLoading
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import (
    instantiate_from_config,
    merge_parameters,
    path_join,
    preprocess_dynamic_configs,
)

if TYPE_CHECKING:
    from mlos_bench.schedulers.base_scheduler import Scheduler
    from mlos_bench.storage.base_storage import Storage


_LOG = logging.getLogger(__name__)


class ConfigPersistenceService(Service, SupportsConfigLoading):
    """Collection of methods to deserialize the Environment, Service, and TunableGroups
    objects.
    """

    BUILTIN_CONFIG_PATH = str(files("mlos_bench.config").joinpath("")).replace("\\", "/")
    """A calculated path to the built-in configuration files shipped with the mlos_bench
    package.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
        methods: dict[str, Callable] | list[Callable] | None = None,
    ):
        """
        Create a new instance of config persistence service.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains parameters for the service.
            (E.g., root path for config files, etc.)
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            An optional parent service that can provide mixin functions.
        methods : Union[dict[str, Callable], list[Callable], None]
            New methods to register with the service.
        """
        super().__init__(
            config,
            global_config,
            parent,
            self.merge_methods(
                methods,
                [
                    self.resolve_path,
                    self.load_config,
                    self.prepare_class_load,
                    self.build_service,
                    self.build_environment,
                    self.load_services,
                    self.load_environment,
                    self.load_environment_list,
                ],
            ),
        )
        self._config_loader_service = self

        # Normalize and deduplicate config paths, but maintain order.
        self._config_path: list[str] = []
        for path in self.config.get("config_path", []):
            if path not in self._config_path:
                self._config_path.append(path_join(path, abs_path=True))
        # Prepend the cwd if not already on the list.
        cwd = path_join(os.getcwd(), abs_path=True)
        if cwd not in self._config_path:
            self._config_path.insert(0, cwd)
        # Append the built-in config path if not already on the list.
        if self.BUILTIN_CONFIG_PATH not in self._config_path:
            self._config_path.append(self.BUILTIN_CONFIG_PATH)

    @property
    def config_paths(self) -> list[str]:
        """
        Gets the list of config paths this service will search for config files.

        Returns
        -------
        list[str]
        """
        return list(self._config_path)  # make a copy to avoid modifications

    def resolve_path(self, file_path: str, extra_paths: Iterable[str] | None = None) -> str:
        """
        Resolves and prepends the suitable :py:attr:`.config_paths` to ``file_path`` if
        the latter is not absolute. If :py:attr:`.config_paths` is ``None`` or
        ``file_path`` is absolute, return ``file_path`` as is.

        Parameters
        ----------
        file_path : str
            Path to the input config file.
        extra_paths : Iterable[str]
            Additional directories to prepend to the list of
            :py:attr:`.config_paths` search paths.

        Returns
        -------
        path : str
            An actual path to the config or script.
        """
        path_list = list(extra_paths or []) + self._config_path
        _LOG.debug("Resolve path: %s in: %s", file_path, path_list)
        if os.path.isabs(file_path):
            _LOG.debug("Path is absolute: %s", file_path)
            return file_path
        for path in path_list:
            full_path = path_join(path, file_path, abs_path=True)
            if os.path.exists(full_path):
                _LOG.debug("Path resolved: %s", full_path)
                return full_path
        _LOG.debug("Path not resolved: %s", file_path)
        return file_path

    def load_config(
        self,
        json: str,
        schema_type: ConfigSchema | None,
    ) -> dict[str, Any]:
        """
        Load JSON config file or JSON string. Search for a file relative to
        :py:attr:`.config_paths` if the input path is not absolute. This method is
        exported to be used as a :py:class:`.SupportsConfigLoading` type
        :py:class:`.Service`.

        Parameters
        ----------
        json : str
            Path to the input config file or a JSON string.
        schema_type : ConfigSchema | None
            The schema type to validate the config against.

        Returns
        -------
        config : Union[dict, list[dict]]
            Free-format dictionary that contains the configuration.
        """
        assert isinstance(json, str)
        if any(c in json for c in ("{", "[")):
            # If the path contains braces, it is likely already a json string,
            # so just parse it.
            _LOG.info("Load config from json string: %s", json)
            try:
                config: Any = json5.loads(json)
            except ValueError as ex:
                _LOG.error("Failed to parse config from JSON string: %s", json)
                raise ValueError(f"Failed to parse config from JSON string: {json}") from ex
        else:
            json = self.resolve_path(json)
            _LOG.info("Load config file: %s", json)
            with open(json, encoding="utf-8") as fh_json:
                config = json5.load(fh_json)
        if schema_type is not None:
            try:
                schema_type.validate(config)
            except (ValidationError, SchemaError) as ex:
                _LOG.error(
                    "Failed to validate config %s against schema type %s at %s",
                    json,
                    schema_type.name,
                    schema_type.value,
                )
                raise ValueError(
                    f"Failed to validate config {json} against "
                    f"schema type {schema_type.name} at {schema_type.value}"
                ) from ex
            if isinstance(config, dict) and config.get("$schema"):
                # Remove $schema attributes from the config after we've validated
                # them to avoid passing them on to other objects
                # (e.g. SqlAlchemy based storage initializers).
                # NOTE: we only do this for internal schemas.
                # Other configs that get loaded may need the schema field
                # (e.g. Azure ARM templates).
                del config["$schema"]
        else:
            _LOG.warning("Config %s is not validated against a schema.", json)
        return config  # type: ignore[no-any-return]

    def prepare_class_load(
        self,
        config: dict[str, Any],
        global_config: dict[str, Any] | None = None,
        parent_args: dict[str, TunableValue] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Extract the class instantiation parameters from the configuration. Mix-in the
        global parameters and resolve the local file system paths, where it is required.

        Parameters
        ----------
        config : dict
            Configuration of the optimizer.
        global_config : dict
            Global configuration parameters (optional).
        parent_args : dict[str, TunableValue]
            An optional reference of the parent CompositeEnv's const_args used to
            expand dynamic config parameters from.

        Returns
        -------
        (class_name, class_config) : (str, dict)
            Name of the class to instantiate and its configuration.
        """
        class_name = config["class"]
        class_config = config.setdefault("config", {})

        # Replace any appearance of "$param_name" in the const_arg values with
        # the value from the parent CompositeEnv.
        # Note: we could consider expanding this feature to additional config
        # sections in the future, but for now only use it in const_args.
        if class_name.startswith("mlos_bench.environments."):
            const_args = class_config.get("const_args", {})
            preprocess_dynamic_configs(dest=const_args, source=parent_args)

        merge_parameters(dest=class_config, source=global_config)

        for key in set(class_config).intersection(config.get("resolve_config_property_paths", [])):
            if isinstance(class_config[key], str):
                class_config[key] = self.resolve_path(class_config[key])
            elif isinstance(class_config[key], (list, tuple)):
                class_config[key] = [self.resolve_path(path) for path in class_config[key]]
            else:
                raise ValueError(f"Parameter {key} must be a string or a list")

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(
                "Instantiating: %s with config:\n%s",
                class_name,
                json5.dumps(class_config, indent=2),
            )

        return (class_name, class_config)

    def build_optimizer(
        self,
        *,
        tunables: TunableGroups,
        service: Service,
        config: dict[str, Any],
        global_config: dict[str, Any] | None = None,
    ) -> Optimizer:
        """
        Instantiation of :py:mod:`mlos_bench` :py:class:`.Optimizer` that depend on
        :py:class:`.Service` and :py:class:`.TunableGroups`.

        Parameters
        ----------
        tunables : TunableGroups
            Tunable parameters of the environment. We need them to validate the
            configurations of merged-in experiments and restored/pending trials.
        service: Service
            An optional service object (e.g., providing methods to load config files, etc.)
        config : dict
            Configuration of the class to instantiate, as loaded from JSON.
        global_config : dict
            Global configuration parameters (optional).

        Returns
        -------
        inst : Optimizer
            A new instance of the `Optimizer` class.
        """
        tunables_path = config.get("include_tunables")
        if tunables_path is not None:
            tunables = self.load_tunables(tunables_path, tunables)
        (class_name, class_config) = self.prepare_class_load(config, global_config)
        inst = instantiate_from_config(
            Optimizer,  # type: ignore[type-abstract]
            class_name,
            tunables=tunables,
            config=class_config,
            global_config=global_config,
            service=service,
        )
        _LOG.info("Created: Optimizer %s", inst)
        return inst

    def build_storage(
        self,
        *,
        service: Service,
        config: dict[str, Any],
        global_config: dict[str, Any] | None = None,
    ) -> "Storage":
        """
        Instantiation of mlos_bench :py:class:`.Storage` objects.

        Parameters
        ----------
        service: Service
            An optional service object (e.g., providing methods to load config files, etc.)
        config : dict
            Configuration of the class to instantiate, as loaded from JSON.
        global_config : dict
            Global configuration parameters (optional).

        Returns
        -------
        inst : Storage
            A new instance of the Storage class.
        """
        (class_name, class_config) = self.prepare_class_load(config, global_config)
        # pylint: disable=import-outside-toplevel
        from mlos_bench.storage.base_storage import Storage

        inst = instantiate_from_config(
            Storage,  # type: ignore[type-abstract]
            class_name,
            config=class_config,
            global_config=global_config,
            service=service,
        )
        _LOG.info("Created: Storage %s", inst)
        return inst

    def build_scheduler(  # pylint: disable=too-many-arguments
        self,
        *,
        config: dict[str, Any],
        global_config: dict[str, Any],
        environment: Environment,
        optimizer: Optimizer,
        storage: "Storage",
        root_env_config: str,
    ) -> "Scheduler":
        """
        Instantiation of mlos_bench :py:class:`.Scheduler`.

        Parameters
        ----------
        config : dict
            Configuration of the class to instantiate, as loaded from JSON.
        global_config : dict
            Global configuration parameters.
        environment : Environment
            The environment to benchmark/optimize.
        optimizer : Optimizer
            The optimizer to use.
        storage : Storage
            The storage to use.
        root_env_config : str
            Path to the root environment configuration.

        Returns
        -------
        inst : Scheduler
            A new instance of the Scheduler.
        """
        (class_name, class_config) = self.prepare_class_load(config, global_config)
        # pylint: disable=import-outside-toplevel
        from mlos_bench.schedulers.base_scheduler import Scheduler

        inst = instantiate_from_config(
            Scheduler,  # type: ignore[type-abstract]
            class_name,
            config=class_config,
            global_config=global_config,
            environment=environment,
            optimizer=optimizer,
            storage=storage,
            root_env_config=root_env_config,
        )
        _LOG.info("Created: Scheduler %s", inst)
        return inst

    def build_environment(
        self,
        config: dict[str, Any],
        tunables: TunableGroups,
        global_config: dict[str, Any] | None = None,
        parent_args: dict[str, TunableValue] | None = None,
        service: Service | None = None,
    ) -> Environment:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Factory method for a new :py:class:`.Environment` with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with three mandatory fields:
                "name": Human-readable string describing the environment;
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        tunables : TunableGroups
            A (possibly empty) collection of groups of tunable parameters for
            all environments.
        global_config : dict
            Global parameters to add to the environment config.
        parent_args : dict[str, TunableValue]
            An optional reference of the parent CompositeEnv's const_args used to
            expand dynamic config parameters from.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).

        Returns
        -------
        env : Environment
            An instance of the ``Environment`` class initialized with ``config``.
        """
        env_name = config["name"]
        (env_class, env_config) = self.prepare_class_load(config, global_config, parent_args)

        env_services_path = config.get("include_services")
        if env_services_path is not None:
            service = self.load_services(env_services_path, global_config, service)

        env_tunables_path = config.get("include_tunables")
        if env_tunables_path is not None:
            tunables = self.load_tunables(env_tunables_path, tunables)

        _LOG.debug("Creating env: %s :: %s", env_name, env_class)
        env = Environment.new(
            env_name=env_name,
            class_name=env_class,
            config=env_config,
            global_config=global_config,
            tunables=tunables,
            service=service,
        )

        _LOG.info("Created env: %s :: %s", env_name, env)
        return env

    def _build_standalone_service(
        self,
        config: dict[str, Any],
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
    ) -> Service:
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with two mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        global_config : dict
            Global parameters to add to the service config.
        parent: Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        svc : Service
            An instance of the `Service` class initialized with `config`.
        """
        (svc_class, svc_config) = self.prepare_class_load(config, global_config)
        service = Service.new(svc_class, svc_config, global_config, parent)
        _LOG.info("Created service: %s", service)
        return service

    def _build_composite_service(
        self,
        config_list: Iterable[dict[str, Any]],
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
    ) -> Service:
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config_list : a list of dict
            A list where each element is a dictionary with 2 mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        global_config : dict
            Global parameters to add to the service config.
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
            service.register(
                self._build_standalone_service(config, global_config, service).export()
            )

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Created mix-in service: %s", service)

        return service

    def build_service(
        self,
        config: dict[str, Any],
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
    ) -> Service:
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with 2 mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        global_config : dict
            Global parameters to add to the service config.
        parent: Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        svc : Service
            An instance of the `Service` class that is a combination of all
            services from the list plus the parent mix-in.
        """
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Build service from config:\n%s", json5.dumps(config, indent=2))

        assert isinstance(config, dict)
        config_list: list[dict[str, Any]]
        if "class" not in config:
            # Top level config is a simple object with a list of services
            config_list = config["services"]
        else:
            # Top level config is a single service
            if parent is None:
                return self._build_standalone_service(config, global_config)
            config_list = [config]

        return self._build_composite_service(config_list, global_config, parent)

    def load_environment(
        self,
        json: str,
        tunables: TunableGroups,
        global_config: dict[str, Any] | None = None,
        parent_args: dict[str, TunableValue] | None = None,
        service: Service | None = None,
    ) -> Environment:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Load and build new :py:class:`.Environment` from the config file or JSON string.

        Parameters
        ----------
        json : str
            The environment JSON configuration file or JSON string.
        tunables : TunableGroups
            A (possibly empty) collection of tunables to add to the environment.
        global_config : dict
            Global parameters to add to the environment config.
        parent_args : dict[str, TunableValue]
            An optional reference of the parent CompositeEnv's const_args used to
            expand dynamic config parameters from.
        service : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        env : Environment
            A new benchmarking environment.
        """
        config = self.load_config(json, ConfigSchema.ENVIRONMENT)
        assert isinstance(config, dict)
        return self.build_environment(config, tunables, global_config, parent_args, service)

    def load_environment_list(
        self,
        json: str,
        tunables: TunableGroups,
        global_config: dict[str, Any] | None = None,
        parent_args: dict[str, TunableValue] | None = None,
        service: Service | None = None,
    ) -> list[Environment]:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Load and build a list of Environments from the config file or JSON string.

        Parameters
        ----------
        json : str
            The environment JSON configuration file or a JSON string.
            Can contain either one environment or a list of environments.
        tunables : TunableGroups
            An (possibly empty) collection of tunables to add to the environment.
        global_config : dict
            Global parameters to add to the environment config.
        service : Service
            An optional reference of the parent service to mix in.
        parent_args : dict[str, TunableValue]
            An optional reference of the parent CompositeEnv's const_args used to
            expand dynamic config parameters from.

        Returns
        -------
        env : list[Environment]
            A list of new benchmarking environments.
        """
        config = self.load_config(json, ConfigSchema.ENVIRONMENT)
        return [self.build_environment(config, tunables, global_config, parent_args, service)]

    def load_services(
        self,
        jsons: Iterable[str],
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
    ) -> Service:
        """
        Read the configuration files or JSON strings and bundle all Service methods from
        those configs into a single Service object.

        Notes
        -----
        Order of the services in the list matters. If multiple Services export the
        same method, the last one in the list will be used.

        Parameters
        ----------
        jsons : list of str
            A list of service JSON configuration files or JSON strings.
        global_config : dict
            Global parameters to add to the service config.
        parent : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        service : Service
            A collection of service methods.
        """
        _LOG.info("Load services: %s parent: %s", jsons, parent.__class__.__name__)
        service = Service({}, global_config, parent)
        for json in jsons:
            config = self.load_config(json, ConfigSchema.SERVICE)
            service.register(self.build_service(config, global_config, service).export())
        return service

    def load_tunables(
        self,
        jsons: Iterable[str],
        parent: TunableGroups | None = None,
    ) -> TunableGroups:
        """
        Load a collection of tunable parameters from JSON files or strings into the
        parent TunableGroup.

        This helps allow standalone environment configs to reference
        overlapping tunable groups configs but still allow combining them into
        a single instance that each environment can reference.

        Parameters
        ----------
        jsons : list of str
            A list of JSON files or JSON strings to load.
        parent : TunableGroups
            A (possibly empty) collection of tunables to add to the new collection.

        Returns
        -------
        tunables : TunableGroups
            The larger collection of tunable parameters.
        """
        _LOG.info("Load tunables: '%s'", jsons)
        if parent is None:
            parent = TunableGroups()
        tunables = parent.copy()
        for json in jsons:
            config = self.load_config(json, ConfigSchema.TUNABLE_PARAMS)
            assert isinstance(config, dict)
            tunables.merge(TunableGroups(config))
        return tunables
