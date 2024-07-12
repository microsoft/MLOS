#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""TunableGroups definition."""
import copy
from typing import Dict, Generator, Iterable, Mapping, Optional, Tuple, Union

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.tunables.covariant_group import CovariantTunableGroup
from mlos_bench.tunables.tunable import Tunable, TunableValue


class TunableGroups:
    """A collection of covariant groups of tunable parameters."""

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
        ConfigSchema.TUNABLE_PARAMS.validate(config)
        # Index (Tunable id -> CovariantTunableGroup)
        self._index: Dict[str, CovariantTunableGroup] = {}
        self._tunable_groups: Dict[str, CovariantTunableGroup] = {}
        for name, group_config in config.items():
            self._add_group(CovariantTunableGroup(name, group_config))

    def __bool__(self) -> bool:
        return bool(self._index)

    def __len__(self) -> int:
        return len(self._index)

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

        Note: non-overlapping groups are expected to be added to the collection.

        Parameters
        ----------
            group : CovariantTunableGroup
        """
        assert (
            group.name not in self._tunable_groups
        ), f"Duplicate covariant tunable group name {group.name} in {self}"
        self._tunable_groups[group.name] = group
        for tunable in group.get_tunables():
            if tunable.name in self._index:
                raise ValueError(
                    f"Duplicate Tunable {tunable.name} from group {group.name} in {self}"
                )
            self._index[tunable.name] = group

    def merge(self, tunables: "TunableGroups") -> "TunableGroups":
        """
        Merge the two collections of covariant tunable groups.

        Unlike the dict `update` method, this method does not modify the
        original when overlapping keys are found.
        It is expected be used to merge the tunable groups referenced by a
        standalone Environment config into a parent CompositeEnvironment,
        for instance.
        This allows self contained, potentially overlapping, but also
        overridable configs to be composed together.

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
        # Check that covariant groups are unique, else throw an error.
        for group in tunables._tunable_groups.values():
            if group.name not in self._tunable_groups:
                self._add_group(group)
            else:
                # Check that there's no overlap in the tunables.
                # But allow for differing current values.
                if not self._tunable_groups[group.name].equals_defaults(group):
                    raise ValueError(
                        f"Overlapping covariant tunable group name {group.name} "
                        "in {self._tunable_groups[group.name]} and {tunables}"
                    )
        return self

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the TunableGroups (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the TunableGroups.
        """
        return (
            "{ "
            + ", ".join(
                f"{group.name}::{tunable}"
                for group in sorted(self._tunable_groups.values(), key=lambda g: (-g.cost, g.name))
                for tunable in sorted(group._tunables.values())
            )
            + " }"
        )

    def __contains__(self, tunable: Union[str, Tunable]) -> bool:
        """Checks if the given name/tunable is in this tunable group."""
        name: str = tunable.name if isinstance(tunable, Tunable) else tunable
        return name in self._index

    def __getitem__(self, tunable: Union[str, Tunable]) -> TunableValue:
        """Get the current value of a single tunable parameter."""
        name: str = tunable.name if isinstance(tunable, Tunable) else tunable
        return self._index[name][name]

    def __setitem__(
        self,
        tunable: Union[str, Tunable],
        tunable_value: Union[TunableValue, Tunable],
    ) -> TunableValue:
        """Update the current value of a single tunable parameter."""
        # Use double index to make sure we set the is_updated flag of the group
        name: str = tunable.name if isinstance(tunable, Tunable) else tunable
        value: TunableValue = (
            tunable_value.value if isinstance(tunable_value, Tunable) else tunable_value
        )
        self._index[name][name] = value
        return self._index[name][name]

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

    def get_tunable(self, tunable: Union[str, Tunable]) -> Tuple[Tunable, CovariantTunableGroup]:
        """
        Access the entire Tunable (not just its value) and its covariant group. Throw
        KeyError if the tunable is not found.

        Parameters
        ----------
        tunable : Union[str, Tunable]
            Name of the tunable parameter.

        Returns
        -------
        (tunable, group) : (Tunable, CovariantTunableGroup)
            A 2-tuple of an instance of the Tunable parameter and covariant group it belongs to.
        """
        name: str = tunable.name if isinstance(tunable, Tunable) else tunable
        group = self._index[name]
        return (group.get_tunable(name), group)

    def get_covariant_group_names(self) -> Iterable[str]:
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
        Select the covariance groups from the current set and create a new TunableGroups
        object that consists of those covariance groups.

        Note: The new TunableGroup will include *references* (not copies) to
        original ones, so each will get updated together.
        This is often desirable to support the use case of multiple related
        Environments (e.g. Local vs Remote) using the same set of tunables
        within a CompositeEnvironment.

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
            if name not in self._tunable_groups:
                raise KeyError(f"Unknown covariant group name '{name}' in tunable group {self}")
            tunables._add_group(self._tunable_groups[name])
        return tunables

    def get_param_values(
        self,
        group_names: Optional[Iterable[str]] = None,
        into_params: Optional[Dict[str, TunableValue]] = None,
    ) -> Dict[str, TunableValue]:
        """
        Get the current values of the tunables that belong to the specified covariance
        groups.

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
            group_names = self.get_covariant_group_names()
        if into_params is None:
            into_params = {}
        for name in group_names:
            into_params.update(self._tunable_groups[name].get_tunable_values_dict())
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
        return any(
            self._tunable_groups[name].is_updated()
            for name in (group_names or self.get_covariant_group_names())
        )

    def is_defaults(self) -> bool:
        """
        Checks whether the currently assigned values of all tunables are at their
        defaults.

        Returns
        -------
        bool
        """
        return all(group.is_defaults() for group in self._tunable_groups.values())

    def restore_defaults(self, group_names: Optional[Iterable[str]] = None) -> "TunableGroups":
        """
        Restore all tunable parameters to their default values.

        Parameters
        ----------
        group_names : list of str or None
            IDs of the (covariant) tunable groups. Restore all groups if omitted.

        Returns
        -------
        self : TunableGroups
            Self-reference for chaining.
        """
        for name in group_names or self.get_covariant_group_names():
            self._tunable_groups[name].restore_defaults()
        return self

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
        for name in group_names or self.get_covariant_group_names():
            self._tunable_groups[name].reset_is_updated()
        return self

    def assign(self, param_values: Mapping[str, TunableValue]) -> "TunableGroups":
        """
        In-place update the values of the tunables from the dictionary of (key, value)
        pairs.

        Parameters
        ----------
        param_values : Mapping[str, TunableValue]
            Dictionary mapping Tunable parameter names to new values.

        Returns
        -------
        self : TunableGroups
            Self-reference for chaining.
        """
        for key, value in param_values.items():
            self[key] = value
        return self
