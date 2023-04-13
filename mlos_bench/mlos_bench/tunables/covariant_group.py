#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tunable parameter definition.
"""
import copy

from typing import Any, Dict, Iterable

from mlos_bench.tunables.tunable import Tunable, TunableValue


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
        self._cost = int(config.get("cost", 0))
        self._tunables: Dict[str, Tunable] = {
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

    def copy(self) -> "CovariantTunableGroup":
        """
        Deep copy of the CovariantTunableGroup object.

        Returns
        -------
        group : CovariantTunableGroup
            A new instance of the CovariantTunableGroup object
            that is a deep copy of the original one.
        """
        return copy.deepcopy(self)

    def __eq__(self, other: object) -> bool:
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
        if not isinstance(other, CovariantTunableGroup):
            return False
        return (self._name == other._name and
                self._cost == other._cost and
                self._is_updated == other._is_updated and
                self._tunables == other._tunables)

    def reset(self) -> None:
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

    def get_names(self) -> Iterable[str]:
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

    def get_tunable(self, name: str) -> Tunable:
        """
        Access the entire Tunable in a group (not just its value).
        Throw KeyError if the tunable is not in the group.

        Parameters
        ----------
        name : str
            Name of the tunable parameter.

        Returns
        -------
        tunable : Tunable
            An instance of the Tunable parameter.
        """
        return self._tunables[name]

    def __getitem__(self, name: str) -> TunableValue:
        return self.get_tunable(name).value

    def __setitem__(self, name: str, value: TunableValue) -> TunableValue:
        self._is_updated = True
        self._tunables[name].value = value
        return value
