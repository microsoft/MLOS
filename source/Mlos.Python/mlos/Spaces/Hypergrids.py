#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
import random
import pandas as pd

from mlos.Exceptions import PointOutOfDomainException
from mlos.Spaces.Dimensions.Dimension import Dimension
from mlos.Spaces.Point import Point


class Hypergrid(ABC):

    def __init__(self, name=None, random_state=None):
        self.name = name
        if random_state is None:
            random_state = random.Random()
        self._random_state = random_state

    @abstractmethod
    def __contains__(self, item):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError

    @property
    @abstractmethod
    def random_state(self):
        return self._random_state

    @random_state.setter
    @abstractmethod
    def random_state(self, value):
        raise NotImplementedError("This has to be implemented in all derived classes to set random_state on individual dimensions.")

    @property
    @abstractmethod
    def dimensions(self):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def get_dimensions_for_point(self, point):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def random(self, point=None):
        raise NotImplementedError("All subclasses must implement this.")

    def random_dataframe(self, num_samples):
        config_dicts = [
            {dim_name: value for dim_name, value in self.random()}
            for _ in range(num_samples)
        ]
        return pd.DataFrame(config_dicts)

    @abstractmethod
    def join(self, subgrid, on_external_dimension: Dimension):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def is_hierarchical(self):
        raise NotImplementedError("All subclasses must implement this.")


class SimpleHypergrid(Hypergrid):
    """ Models a space comprized of Continuous, Discrete, Ordinal and Categorical Dimensions.

    Can be flat or hierarchical, depending if any join operations were performed.

    Parameters
    ----------
    name : str
        Identifier

    dimensions : list of Dimension
        List of dimension objects. The space is the cartesian product of these.

    """
    class GuestSubgrid:
        """ Allows a subgrid to be joined on a dimension that's not in that subgrid.

        Think how in SQL you can do:
            SELECT * FROM Employee JOIN Employer ON Employee.Name = 'John';
        The JOIN predicate does not reference any column in Employer so we end up with a cross product of all John's with
        all employers.

        That's kinda the idea here. We want to join a subgrid on an arbitrary predicate expressed by that external_pivot_dimension.
        """
        def __init__(self, subgrid, external_pivot_dimension):
            self.subgrid = subgrid
            self.external_pivot_dimension = external_pivot_dimension

    def __init__(self, name, dimensions=None, random_state=None):
        Hypergrid.__init__(self, name=name, random_state=random_state)
        self._dimensions = []
        self.dimensions_dict = dict()

        if dimensions is None:
            dimensions = []

        for dimension in dimensions:
            self.add_dimension(dimension)

        # maps a pivot dimension name to a set of guest subgrids that are joined on that external dimension
        #
        self.guest_subgrids_by_pivot_dimension = dict()

        # maps a subgrid name to the subgrid
        #
        self.subgrids_by_name = dict()

    def is_hierarchical(self):
        return len(self.subgrids_by_name) > 0

    def add_dimension(self, dimension):
        assert isinstance(dimension, Dimension)
        assert dimension.name not in self.dimensions_dict

        dimension.random_state = self.random_state
        self.dimensions_dict[dimension.name] = dimension
        self._dimensions.append(dimension)

    @property
    def random_state(self):
        return self._random_state

    @random_state.setter
    def random_state(self, value):
        self._random_state = value
        for dimension in self._dimensions:
            dimension.random_state = self._random_state
        for _, subgrid in self.subgrids_by_name.items():
            subgrid.random_state = self.random_state

    def __getitem__(self, dimension_name):
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(dimension_name)
        if subgrid_name is None:
            return self.dimensions_dict.get(dimension_name, None)
        subgrid = self.subgrids_by_name[subgrid_name]
        return subgrid[dimension_name_without_subgrid_name]


    def __repr__(self):
        ret = [f"{self.name}"]
        for dimension in self.dimensions:
            ret.append(str(dimension))
        return "\n".join(ret)

    def add_subgrid_on_external_dimension(self, other_hypergrid: Hypergrid, external_dimension: Dimension):
        assert external_dimension.name in self.dimensions_dict, f"{self.name} does not contain dimension {external_dimension.name}"
        if not self[external_dimension.name].intersects(external_dimension):
            # They don't intersect so nothing to do
            return

        guest_subgrids_joined_on_dimension = self.guest_subgrids_by_pivot_dimension.get(external_dimension.name, set())
        if any(guest_subgrid.subgrid.name == other_hypergrid.name for guest_subgrid in guest_subgrids_joined_on_dimension):
            raise RuntimeError(f"Subgrid {other_hypergrid.name} already joined to hypergrid {self.name} along the dimension {external_dimension.name}.")

        other_hypergrid.random_state = self.random_state
        guest_subgrids_joined_on_dimension.add(SimpleHypergrid.GuestSubgrid(subgrid=other_hypergrid, external_pivot_dimension=external_dimension))
        self.guest_subgrids_by_pivot_dimension[external_dimension.name] = guest_subgrids_joined_on_dimension
        self.subgrids_by_name[other_hypergrid.name] = other_hypergrid

    def __contains__(self, item):
        if isinstance(item, Point):
            return self.contains_point(point=item)
        raise NotImplementedError

    def join(self, subgrid: Hypergrid, on_external_dimension: Dimension):
        """ Joins the subgrid on the specified dimension.

        :param subgrid:
        :param on_external_dimension:
        :return:
        """
        assert on_external_dimension is not None

        external_dimension = on_external_dimension
        pivot_dimension_name = external_dimension.name
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(pivot_dimension_name)
        if subgrid_name is None:
            self.add_subgrid_on_external_dimension(other_hypergrid=subgrid, external_dimension=external_dimension)
        else:
            existing_subgrid = self.subgrids_by_name.get(subgrid_name, None)
            assert existing_subgrid is not None
            external_dimension = external_dimension.copy()
            external_dimension.name = dimension_name_without_subgrid_name
            self.subgrids_by_name[subgrid_name] = existing_subgrid.join(
                subgrid=subgrid,
                on_external_dimension=external_dimension
            )
        return self

    def contains_point(self, point: Point):
        """ Checks if point belongs to the  hypergrid.

        We must first see if for every dimension of the root hypergrid, the Point:
        a) specifies the dimension
        b) the value along that dimension is within bounds

        Then for every pivotal dimension present in the point we must:
        a) find the corresponding subgrid that might have been joined
        b) check if the value along pivotal dimension belongs to that subgrid
        c) if b) is true, then for every dimension in the subgrid, check if the points dimension
            values are within bounds.

        This has to be recursive, because any of the subgrids can be hierarchical already.

        :param point:
        :return:
        """

        if not all(point[dimension.name] is not None and point[dimension.name] in dimension for dimension in self._dimensions):
            return False

        for external_dimension_name, guest_subgrids_joined_on_dimension in self.guest_subgrids_by_pivot_dimension.items():
            for guest_subgrid in guest_subgrids_joined_on_dimension:
                if point[external_dimension_name] in guest_subgrid.external_pivot_dimension:
                    # We need to check if the sub_point belongs to the sub_grid
                    #
                    subgrid = guest_subgrid.subgrid
                    if subgrid.name not in point or point[subgrid.name] not in subgrid:
                        return False
        return True


    def contains_space(self, other_space):
        """ Checks if other_space is a subspace of this one.

        For another space to be a subspace of this one:
            1. all of the other_space.dimensions must be in self.dimensions
            2. every dimension in other_space.dimensions must be contained by the corresponding dimension in this space.

        However the complication arises for hierarchical hypergrids so we'll tackle this more complex problem down the road.

        :param other_space:
        :return:
        """
        if self.is_hierarchical() or other_space.is_hierarchical():
            raise NotImplementedError

        for other_dimension in other_space.dimensions:
            our_dimension = self.dimensions_dict.get(other_dimension.name, None)
            if our_dimension is None:
                return False
            if other_dimension not in our_dimension:
                return False
        return True

    def random(self, point=None):
        if point is None:
            point = Point()

        for dimension in self._dimensions:
            if dimension.name not in point:
                point[dimension.name] = dimension.random()

        for external_dimension_name, guest_subgrids_joined_on_dimension in self.guest_subgrids_by_pivot_dimension.items():
            for guest_subgrid in guest_subgrids_joined_on_dimension:
                if point[external_dimension_name] in guest_subgrid.external_pivot_dimension:
                    sub_point = guest_subgrid.subgrid.random()
                    point[guest_subgrid.subgrid.name] = sub_point

        return point

    @property
    def dimensions(self):
        dimensions = []
        for dimension in self._dimensions:
            dimensions.append(dimension)
        for subgrid_name, subgrid in self.subgrids_by_name.items():
            for dimension in subgrid.dimensions:
                returned_dimension = dimension.copy()
                returned_dimension.name = subgrid_name + "." + returned_dimension.name
                dimensions.append(returned_dimension)
        return dimensions

    @property
    def root_dimensions(self):
        return self._dimensions

    def get_dimensions_for_point(self, point):
        """ Returns dimensions that the given point and belongs to. For pivot dimensions, it returns the guest_subgrid.external_pivot_dimension

        In a hierarchical hypergrid, coordiantes of a point in the root hypergrid determine which of the subgrids will be 'activated' (meaningful). For example
        if point.base_boosting_regression_model_name == "LassoRegression" then the subgrid describing the configuration for Lasso Regression becomes 'activated'
        that is to say, specifying parameters for Lasso Regression becomes meaningful. If point.base_boosting_regression_model_name == "RidgeRegression", we can
        still specify the Lasso Regression parameters, but they would never be consumed (by the smart component) so are meaningless and effectively noise.

        :param point:
        :return:
        """
        if point not in self:
            raise PointOutOfDomainException(f"Point {point} does not belong to {self}.")

        dimensions_by_name = {dimension.name: dimension for dimension in self._dimensions}
        ordered_dimension_names = [dimension.name for dimension in self._dimensions]

        for external_dimension_name, guest_subgrids_joined_on_dimension in self.guest_subgrids_by_pivot_dimension.items():
            for guest_subgrid in guest_subgrids_joined_on_dimension:
                if point[external_dimension_name] in guest_subgrid.external_pivot_dimension:
                    # We return this narrower pivot dimension, since point[external_dimension_name] has
                    # to belong to the external_pivot_dimension for all of the subgrid dimensions to make sense.
                    #
                    dimensions_by_name[external_dimension_name] = guest_subgrid.external_pivot_dimension
                    subgrid = guest_subgrid.subgrid
                    for dimension in subgrid.get_dimensions_for_point(point[subgrid.name]):
                        dimension = dimension.copy()
                        dimension.name = f"{subgrid.name}.{dimension.name}"
                        dimensions_by_name[dimension.name] = dimension
                        ordered_dimension_names.append(dimension.name)

        # Returning dimensions in order they were visited (mostly to make sure that root dimension names come first.
        #
        return [dimensions_by_name[name] for name in ordered_dimension_names]
