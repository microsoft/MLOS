"""
A hierarchy of benchmark environments.
"""

import abc
import json
import logging
import importlib

from mlos_bench.environment.status import Status
from mlos_bench.environment.tunable import TunableGroups

_LOG = logging.getLogger(__name__)


class Environment(metaclass=abc.ABCMeta):
    """
    An abstract base of all benchmark environments.
    """

    @classmethod
    def new(cls, env_name, class_name, config, tunables=None, service=None):    # pylint: disable=too-many-arguments
        """
        Factory method for a new environment with a given config.

        Parameters
        ----------
        env_name: str
            Human-readable name of the environment.
        class_name: str
            FQN of a Python class to instantiate, e.g.,
            "mlos_bench.environment.azure.VMEnv".
            Must be derived from the `Environment` class.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. It will be passed as a constructor parameter of
            the class specified by `name`.
        tunables : TunableGroups
            A collection of groups of tunable parameters for all environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).

        Returns
        -------
        env : Environment
            An instance of the `Environment` class initialized with `config`.
        """
        # We need to import mlos_bench to make the factory methods
        # like `Environment.new()` work.
        class_name_split = class_name.split(".")
        module_name = ".".join(class_name_split[:-1])
        class_id = class_name_split[-1]

        env_module = importlib.import_module(module_name)
        env_class = getattr(env_module, class_id)

        _LOG.info("Instantiating: %s :: class %s = %s",
                  env_name, class_name, env_class)

        assert issubclass(env_class, cls)
        return env_class(env_name, config, tunables, service)

    def __init__(self, name, config, tunables=None, service=None):
        """
        Create a new environment with a given config.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections; the "cost" field can be omitted
            and is 0 by default.
        tunables : TunableGroups
            A collection of groups of tunable parameters for all environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
        """
        self.name = name
        self.config = config
        self._service = service
        self._result = (Status.PENDING, None)

        self._const_args = config.get("const_args", {})

        if tunables is None:
            tunables = TunableGroups()

        tunable_groups = config.get("tunable_params")
        self._tunable_params = (
            tunables.subgroup(tunable_groups) if tunable_groups else tunables
        )

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Config for: %s\n%s",
                       name, json.dumps(self.config, indent=2))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Env: {self.__class__} :: '{self.name}'"

    def _combine_tunables(self, tunables):
        """
        Plug tunable values into the base config. If the tunable group is unknown,
        ignore it (it might belong to another environment). This method should
        never mutate the original config or the tunables.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters
            along with the parameters' values.

        Returns
        -------
        config : dict
            Free-format dictionary that contains the new environment configuration.
        """
        return tunables.get_param_values(
            group_names=self._tunable_params.get_names(),
            into_params=self._const_args.copy())

    def tunable_params(self):
        """
        Get the configuration space of the given environment.

        Returns
        -------
        tunables : TunableGroups
            A collection of covariant groups of tunable parameters.
        """
        return self._tunable_params

    def setup(self): # pylint: disable=no-self-use
        """
        Set up a new benchmark environment, if necessary. This method must be
        idempotent, i.e., calling it several times in a row should be
        equivalent to a single call.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        return True

    def teardown(self): # pylint: disable=no-self-use
        """
        Tear down the benchmark environment. This method must be idempotent,
        i.e., calling it several times in a row should be equivalent to a
        single call.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        return True

    @abc.abstractmethod
    def run(self, tunables):
        """
        Submit a new experiment to the environment.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of tunable parameters along with their values.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """

    def submit(self, tunables):
        """
        Submit a new experiment to the environment. Set up the environment,
        if necessary.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of tunable parameters along with their values.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Submit: %s", tunables)
        if self.setup():
            return self.run(tunables)
        return False

    def status(self):
        """
        Get the status of the environment.

        Returns
        -------
        status : mlos_bench.environment.Status
            Current status of the benchmark environment.
        """
        return self._result[0]

    def result(self):
        """
        Get the results of the benchmark. This is a blocking call that waits
        for the completion of the benchmark. It can have PENDING status only if
        the environment object has been read from the storage and not updated
        with the actual status yet.

        Base implementation returns the results of the last .update() call.

        Returns
        -------
        (benchmark_status, benchmark_result) : (enum, float)
            A pair of (benchmark status, benchmark result) values.
            benchmark_status is one one of:
                PENDING
                RUNNING
                COMPLETED
                CANCELED
                FAILED
            benchmark_result is a floating point time of the benchmark in
            seconds or None if the status is not COMPLETED.
        """
        _LOG.info("Result: %s", self._result)
        return self._result
