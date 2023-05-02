#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tunable parameter definition.
"""
import copy

from typing import Dict, Iterable, Union

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

    @property
    def cost(self) -> int:
        """
        Get the cost of changing the values in the covariant group.
        This value is a constant. Use `get_current_cost()` to get
        the cost given the group update status.

        Returns
        -------
        cost : int
            Cost of changing the values in the covariant group.
        """
        return self._cost

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

    def get_current_cost(self) -> int:
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

    def get_tunable_values_dict(self) -> Dict[str, TunableValue]:
        """
        Get current values of all tunables in the group as a dict.

        Returns
        -------
        tunables : Dict[str, TunableValue]
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

    def get_tunable(self, tunable: Union[str, Tunable]) -> Tunable:
        """
        Access the entire Tunable in a group (not just its value).
        Throw KeyError if the tunable is not in the group.

        Parameters
        ----------
        tunable : str
            Name of the tunable parameter.

        Returns
        -------
        Tunable
            An instance of the Tunable parameter.
        """
        name: str = tunable.name if isinstance(tunable, Tunable) else tunable
        return self._tunables[name]

    def get_tunables(self) -> Iterable[Tunable]:
        """Gets the set of tunables for this CovariantTunableGroup.

        Returns
        -------
        Iterable[Tunable]
        """
        return self._tunables.values()

    def __contains__(self, tunable: Union[str, Tunable]) -> bool:
        name: str = tunable.name if isinstance(tunable, Tunable) else tunable
        return name in self._tunables

    def __getitem__(self, tunable: Union[str, Tunable]) -> TunableValue:
        return self.get_tunable(tunable).value

    def __setitem__(self, tunable: Union[str, Tunable], tunable_value: Union[TunableValue, Tunable]) -> TunableValue:
        self._is_updated = True
        name: str = tunable.name if isinstance(tunable, Tunable) else tunable
        value: TunableValue = tunable_value.value if isinstance(tunable_value, Tunable) else tunable_value
        self._tunables[name].value = value
        return value
