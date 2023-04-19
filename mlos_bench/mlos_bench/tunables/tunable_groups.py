#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
TunableGroups definition.
"""
import copy

from typing import Any, Dict, Generator, Iterable, Optional, Tuple

from mlos_bench.tunables.tunable import Tunable, TunableValue
from mlos_bench.tunables.covariant_group import CovariantTunableGroup


class TunableGroups:
    """
    A collection of covariant groups of tunable parameters.
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Create a new group of tunable parameters.

        Parameters
        ----------
        config : dict
            Python dict of serialized representation of the covariant tunable groups.
        """
        if config is None:
            config = {}
        self._index: Dict[str, CovariantTunableGroup] = {}  # Index (Tunable id -> CovariantTunableGroup)
        self._tunable_groups: Dict[str, CovariantTunableGroup] = {}
        for (name, group_config) in config.items():
            self._add_group(CovariantTunableGroup(name, group_config))

    def __eq__(self, other: object) -> bool:
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
        if not isinstance(other, TunableGroups):
            return False
        return bool(self._tunable_groups == other._tunable_groups)

    def copy(self) -> "TunableGroups":
        """
        Deep copy of the TunableGroups object.

        Returns
        -------
        tunables : TunableGroups
            A new instance of the TunableGroups object
            that is a deep copy of the original one.
        """
        return copy.deepcopy(self)

    def _add_group(self, group: CovariantTunableGroup) -> None:
        """
        Add a CovariantTunableGroup to the current collection.

        Parameters
        ----------
            group : CovariantTunableGroup
        """
        self._tunable_groups[group.name] = group
        self._index.update(dict.fromkeys(group.get_names(), group))

    def update(self, tunables: "TunableGroups") -> "TunableGroups":
        """
        Merge the two collections of covariant tunable groups.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of covariant tunable groups.

        Returns
        -------
        self : TunableGroups
            Self-reference for chaining.
        """
        # pylint: disable=protected-access
        self._index.update(tunables._index)
        self._tunable_groups.update(tunables._tunable_groups)
        return self

    def __repr__(self) -> str:
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

    def __getitem__(self, name: str) -> TunableValue:
        """
        Get the current value of a single tunable parameter.
        """
        return self._index[name][name]

    def __setitem__(self, name: str, value: TunableValue) -> None:
        """
        Update the current value of a single tunable parameter.
        """
        # Use double index to make sure we set the is_updated flag of the group
        self._index[name][name] = value

    def __iter__(self) -> Generator[Tuple[Tunable, CovariantTunableGroup], None, None]:
        """
        An iterator over all tunables in the group.

        Returns
        -------
        [(tunable, group), ...] : iter(Tunable, CovariantTunableGroup)
            An iterator over all tunables in all groups. Each element is a 2-tuple
            of an instance of the Tunable parameter and covariant group it belongs to.
        """
        return ((group.get_tunable(name), group) for (name, group) in self._index.items())

    def get_tunable(self, name: str) -> Tuple[Tunable, CovariantTunableGroup]:
        """
        Access the entire Tunable (not just its value) and its covariant group.
        Throw KeyError if the tunable is not found.

        Parameters
        ----------
        name : str
            Name of the tunable parameter.

        Returns
        -------
        (tunable, group) : (Tunable, CovariantTunableGroup)
            A 2-tuple of an instance of the Tunable parameter and covariant group it belongs to.
        """
        group = self._index[name]
        return (group.get_tunable(name), group)

    def get_names(self) -> Iterable[str]:
        """
        Get the names of all covariance groups in the collection.

        Returns
        -------
        group_names : [str]
            IDs of the covariant tunable groups.
        """
        return self._tunable_groups.keys()

    def subgroup(self, group_names: Iterable[str]) -> "TunableGroups":
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

    def get_param_values(self, group_names: Optional[Iterable[str]] = None,
                         into_params: Optional[Dict[str, Any]] = None) -> Dict[str, TunableValue]:
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

    def is_updated(self, group_names: Optional[Iterable[str]] = None) -> bool:
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

    def reset(self, group_names: Optional[Iterable[str]] = None) -> "TunableGroups":
        """
        Clear the update flag of given covariant groups.

        Parameters
        ----------
        group_names : list of str or None
            IDs of the (covariant) tunable groups. Reset all groups if omitted.

        Returns
        -------
        self : TunableGroups
            Self-reference for chaining.
        """
        for name in (group_names or self.get_names()):
            self._tunable_groups[name].reset()
        return self

    def assign(self, param_values: Dict[str, Any]) -> "TunableGroups":
        """
        In-place update the values of the tunables from the dictionary
        of (key, value) pairs.

        Parameters
        ----------
        param_values : Dict[str, Any]
            Dictionary mapping Tunable parameter names to new values.

        Returns
        -------
        self : TunableGroups
            Self-reference for chaining.
        """
        for key, value in param_values.items():
            self[key] = value
        return self
