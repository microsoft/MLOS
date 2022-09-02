"""
Tunable parameter definition.
"""
import collections
from typing import Any, Dict, List


class Tunable:  # pylint: disable=too-many-instance-attributes
    """
    A tunable parameter definition and its current value.
    """

    def __init__(self, name, config):
        """
        Create an instance of a new tunable parameter.

        Parameters
        ----------
        name : str
            Human-readable identifier of the tunable parameter.
        config : dict
            Python dict that represents a Tunable (e.g., deserialized from JSON)
        """
        self._name = name
        self._description = config.get("description")
        self._type = config["type"]
        self._default = config.get("default")
        self._values = config.get("values")
        self._range = config.get("range")
        self._special = config.get("special")
        self._current_value = self._default
        if self._type == "categorical":
            if not (self._values and isinstance(self._values, collections.abc.Iterable)):
                raise ValueError("Must specify values for the categorical type")
            if self._range is not None:
                raise ValueError("Range must be None for the categorical type")
            if self._special is not None:
                raise ValueError("Special values must be None for the categorical type")
        elif self._type in {"int", "float"}:
            if not self._range or len(self._range) != 2 or self._range[0] >= self._range[1]:
                raise ValueError("Invalid range: " + self._range)
        else:
            raise ValueError("Invalid parameter type: " + self._type)

    def __repr__(self):
        return f"{self._name}={self._current_value}"

    @property
    def value(self):
        """
        Get the current value of the tunable.
        """
        return self._current_value

    @value.setter
    def value(self, value):
        """
        Set the current value of the tunable.
        """
        self._current_value = value
        return value


class CovariantTunableGroup:
    """
    A collection of tunable parameters.
    Changing any of the parameters in the group incurs the same cost of the experiment.
    """

    def __init__(self, name, config):
        """
        Create a new group of tunable parameters.

        Parameters
        ----------
        name : str
            Human-readable identifier of the tunable parameters group.
        config : dict
            Python dict that represents a CovariantTunableGroup
            (e.g., deserialized from JSON).
        """
        self._is_updated = True
        self._name = name
        self._cost = config.get("cost", 0)
        self._tunables = {
            name: Tunable(name, tunable_config)
            for (name, tunable_config) in config.get("params", {}).items()
        }

    def reset(self):
        """
        Clear the update flag. That is, state that running an experiment with the
        current values of the tunables in this group has no extra cost.
        """
        self._is_updated = False

    def get_cost(self):
        """
        Get the cost of the experiment given current tunable values.

        Returns
        -------
        cost : int
            Cost of the experiment or 0 if parameters have not been updated.
        """
        return self._cost if self._is_updated else 0

    def get_names(self):
        """
        Get the names of all tunables in the group.
        """
        return self._tunables.keys()

    def get_values(self):
        """
        Get current values of all tunables in the group.
        """
        return {name: tunable.value for (name, tunable) in self._tunables.items()}

    def __repr__(self):
        return f"{self._name}: {self._tunables}"

    def __getitem__(self, name):
        return self._tunables[name].value

    def __setitem__(self, name, value):
        self._is_updated = True
        self._tunables[name].value = value
        return value


class TunableGroups:
    """
    A collection of covariant groups of tunable parameters.
    """

    def __init__(self, config=None):
        """
        Create a new group of tunable parameters.

        Parameters
        ----------
        config : dict
            Python dict of serialized representation of the covariant tunable groups.
        """
        self._index = {}  # Index (Tunable id -> CovariantTunableGroup)
        self._tunable_groups = {}
        for (name, group_config) in (config or {}).items():
            self._add_group(CovariantTunableGroup(name, group_config))

    def _add_group(self, group):
        """
        Add a CovariantTunableGroup to the current collection.

        Parameters
        ----------
            group : CovariantTunableGroup
        """
        # pylint: disable=protected-access
        self._tunable_groups[group._name] = group
        self._index.update(dict.fromkeys(group.get_names(), group))

    def update(self, tunables):
        """
        Merge the two collections of covariant tunable groups.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of covariant tunable groups.
        """
        # pylint: disable=protected-access
        self._index.update(tunables._index)
        self._tunable_groups.update(tunables._tunable_groups)

    def __repr__(self):
        return "{ " + ", ".join(
            f"{group_name}::{tunable}"
            for (group_name, group) in self._tunable_groups.items()
            for tunable in group._tunables.values()) + " }"

    def __getitem__(self, name):
        """
        Get the current value of a single tunable parameter.
        """
        return self._index[name][name]

    def __setitem__(self, name, value):
        """
        Update the current value of a single tunable parameter.
        """
        # Use double index to make sure we set the is_updated flag of the group
        self._index[name][name] = value

    def get_names(self):
        """
        Get the names of all covariance groups in the collection.

        Returns
        -------
        group_names : [str]
            IDs of the covariant tunable groups.
        """
        return self._tunable_groups.keys()

    def subgroup(self, group_names: List[str]):
        """
        Select the covariance groups from the current set and create a new
        TunableGroups object that consists of those covariance groups.

        Parameters
        ----------
        group_names : list of str
            IDs of the covariant tunable groups.

        Returns
        -------
        tunables : TunableGroups
            A collection of covariant tunable groups.
        """
        # pylint: disable=protected-access
        tunables = TunableGroups()
        for name in group_names:
            tunables._add_group(self._tunable_groups[name])
        return tunables

    def get_param_values(self, group_names: List[str] = None, into_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get the current values of the tunables that belong to the specified covariance groups.

        Parameters
        ----------
        group_names : list of str or None
            IDs of the covariant tunable groups.
            Select parameters from all groups if omitted.
        into_params : dict
            An optional dict to copy the parameters and their values into.

        Returns
        -------
        into_params : dict
            Flat dict of all parameters and their values from given covariance groups.
        """
        if group_names is None:
            group_names = self.get_names()
        if into_params is None:
            into_params = {}
        for name in group_names:
            into_params.update(self._tunable_groups[name].get_values())
        return into_params

    def reset(self, group_names: List[str] = None):
        """
        Clear the update flag of given covariant groups.

        Parameters
        ----------
        group_names : list of str or None
            IDs of the (covariant) tunable groups. Reset all groups if omitted.
        """
        for name in (group_names or self.get_names()):
            self._tunable_groups[name].reset()
