"""
Tunable parameter definition.
"""
import copy
import collections

from typing import Any, Dict, List


class Tunable:  # pylint: disable=too-many-instance-attributes
    """
    A tunable parameter definition and its current value.
    """

    def __init__(self, name: str, config: dict):
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
        self._type = config["type"]  # required
        self._description = config.get("description")
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

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the Tunable (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the Tunable.
        """
        return f"{self._name}={self._current_value}"

    def __eq__(self, other) -> bool:
        """
        Check if two Tunable objects are equal.

        Parameters
        ----------
        other : Tunable
            A tunable object to compare to.

        Returns
        -------
        is_equal : bool
            True if the Tunables correspond to the same parameter and have the same value and type.
            NOTE: ranges and special values are not currently considered in the comparison.
        """
        return (
            self._name == other._name and
            self._type == other._type and
            self._current_value == other._current_value
        )

    def copy(self):
        """
        Deep copy of the Tunable object.

        Returns
        -------
        tunable : Tunable
            A new Tunable object that is a deep copy of the original one.
        """
        return copy.deepcopy(self)

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

    def __init__(self, name: str, config: dict):
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

    @property
    def name(self) -> str:
        """
        Get the name of the covariant group.

        Returns
        -------
        name : str
            Name (i.e., a string id) of the covariant group.
        """
        return self._name

    def copy(self):
        """
        Deep copy of the CovariantTunableGroup object.

        Returns
        -------
        group : CovariantTunableGroup
            A new instance of the CovariantTunableGroup object
            that is a deep copy of the original one.
        """
        return copy.deepcopy(self)

    def __eq__(self, other) -> bool:
        """
        Check if two CovariantTunableGroup objects are equal.

        Parameters
        ----------
        other : CovariantTunableGroup
            A covariant tunable group object to compare to.

        Returns
        -------
        is_equal : bool
            True if two CovariantTunableGroup objects are equal.
        """
        return (self._name == other._name and
                self._cost == other._cost and
                self._is_updated == other._is_updated and
                all(t1 == t2 for (t1, t2) in zip(self._tunables.values(),
                                                 other._tunables.values())))

    def reset(self):
        """
        Clear the update flag. That is, state that running an experiment with the
        current values of the tunables in this group has no extra cost.
        """
        self._is_updated = False

    def is_updated(self) -> bool:
        """
        Check if any of the tunable values in the group has been updated.

        Returns
        -------
        is_updated : bool
            True if any of the tunable values in the group has been updated, False otherwise.
        """
        return self._is_updated

    def get_cost(self) -> int:
        """
        Get the cost of the experiment given current tunable values.

        Returns
        -------
        cost : int
            Cost of the experiment or 0 if parameters have not been updated.
        """
        return self._cost if self._is_updated else 0

    def get_names(self) -> List[str]:
        """
        Get the names of all tunables in the group.
        """
        return self._tunables.keys()

    def get_values(self) -> Dict[str, Any]:
        """
        Get current values of all tunables in the group.
        """
        return {name: tunable.value for (name, tunable) in self._tunables.items()}

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the CovariantTunableGroup
        (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the CovariantTunableGroup.
        """
        return f"{self._name}: {self._tunables}"

    def __getitem__(self, name: str):
        return self._tunables[name].value

    def __setitem__(self, name: str, value):
        self._is_updated = True
        self._tunables[name].value = value
        return value


class TunableGroups:
    """
    A collection of covariant groups of tunable parameters.
    """

    def __init__(self, config: dict = None):
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

    def __eq__(self, other) -> bool:
        """
        Check if two TunableGroups are equal.

        Parameters
        ----------
        other : TunableGroups
            A tunable groups object to compare to.

        Returns
        -------
        is_equal : bool
            True if two TunableGroups are equal.
        """
        return all(g1 == g2 for (g1, g2) in zip(self._tunable_groups.values(),
                                                other._tunable_groups.values()))

    def copy(self):
        """
        Deep copy of the TunableGroups object.

        Returns
        -------
        tunables : TunableGroups
            A new instance of the TunableGroups object
            that is a deep copy of the original one.
        """
        return copy.deepcopy(self)

    def _add_group(self, group: CovariantTunableGroup):
        """
        Add a CovariantTunableGroup to the current collection.

        Parameters
        ----------
            group : CovariantTunableGroup
        """
        self._tunable_groups[group.name] = group
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
        """
        Produce a human-readable version of the TunableGroups (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the TunableGroups.
        """
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

    def get_names(self) -> List[str]:
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

    def get_param_values(self, group_names: List[str] = None,
                         into_params: Dict[str, Any] = None) -> Dict[str, Any]:
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

    def is_updated(self, group_names: List[str] = None) -> bool:
        """
        Check if any of the given covariant tunable groups has been updated.

        Parameters
        ----------
        group_names : list of str or None
            IDs of the (covariant) tunable groups. Check all groups if omitted.

        Returns
        -------
        is_updated : bool
            True if any of the specified tunable groups has been updated, False otherwise.
        """
        return any(self._tunable_groups[name].is_updated()
                   for name in (group_names or self.get_names()))

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

    def assign(self, param_values: Dict[str, Any]):
        """
        In-place update the values of the tunables from the dictionary
        of (key, value) pairs.

        Parameters
        ----------
        param_values : Dict[str, Any]
            Dictionary mapping Tunable parameter names to new values.
        """
        for key, value in param_values.items():
            self[key] = value
