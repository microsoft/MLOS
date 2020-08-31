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


class SimpleHypergrid(Hypergrid):
    """ Models a space comprized of Continuous, Discrete, Ordinal and Categorical Dimensions

    """

    def __init__(self, name, dimensions=None, random_state=None):
        super(SimpleHypergrid, self).__init__(name=name, random_state=random_state)
        if dimensions is None:
            dimensions = []
        self._dimensions = []
        self.dimensions_dict = dict()

        for dimension in dimensions:
            dimension.random_state = self.random_state
            self.add_dimension(dimension)

    def __str__(self):
        return f"{self.name} = {' x '.join('{' + str(dimension) + '}' for dimension in self._dimensions)}"

    @property
    def random_state(self):
        return self._random_state

    @random_state.setter
    def random_state(self, value):
        self._random_state = value
        for dimension in self._dimensions:
            dimension.random_state = self.random_state

    @property
    def dimensions(self):
        return self._dimensions

    @property
    def num_dimensions(self):
        return len(self._dimensions)

    def get_dimensions_for_point(self, point):
        """ Returns a list of dimensions for a given point.

        It's trivial for SimpleHypergrid, but more interesting for the

        :param point:
        :return:
        """
        if point not in self:
            raise PointOutOfDomainException(f"Point {point} does not belong to {self}.")

        return self.dimensions


    def add_dimension(self, dimension):
        assert isinstance(dimension, Dimension)
        assert dimension.name not in self.dimensions_dict

        dimension.random_state = self.random_state
        self.dimensions_dict[dimension.name] = dimension
        self._dimensions.append(dimension)

    def __contains__(self, item):
        if isinstance(item, Hypergrid):
            return self.contains_space(item)
        if isinstance(item, Point):
            return self.contains_point(item)
        raise NotImplementedError(f"SimpleHypergrid only supports containment operator for SimpleHypergrids and Points, not {type(item)}")

    def intersects(self, other_space):
        """ Determines if self intersects with the other_space.

        The only way they don't intersect is if there is at least one dimension common to both spaces that
        such that self[dimension.name].intersects(other[dimension.name) == False.

        :param other_space:
        :return:
        """
        assert isinstance(other_space, SimpleHypergrid)
        for other_dimension in other_space.dimensions:
            our_dimension = self[other_dimension.name]
            if our_dimension is None:
                continue
            if not our_dimension.intersects(other_dimension):
                return False
        return True

    def join(self, subgrid: Hypergrid, on_external_dimension: Dimension):
        """ Creates a CompositeHypergrid with itself as a root.
        """
        assert on_external_dimension is not None
        external_dimension = on_external_dimension

        assert self[external_dimension.name] is not None, f"The {self.name} hypergrid does not contain dimension named {external_dimension.name}."
        if not self[external_dimension.name].intersects(external_dimension):
            # No intersection - nothing to do
            return self
        hierarchical_space = CompositeHypergrid(name=self.name, root_hypergrid=self)
        hierarchical_space.add_subgrid_on_external_dimension(other_hypergrid=subgrid, external_dimension=external_dimension)
        return hierarchical_space

    def __getitem__(self, dimension_name):
        return self.dimensions_dict.get(dimension_name, None)

    def contains_space(self, other_space):
        """ Checks if other_space is a subspace of this one.

        For another space to be a subspace of this one:
            1. all of the other_space.dimensions must be in self.dimensions
            2. every dimension in other_space.dimensions must be contained by the corresponding dimension in this space.

        :param other_space:
        :return:
        """

        for other_dimension in other_space.dimensions:
            our_dimension = self.dimensions_dict.get(other_dimension.name, None)
            if our_dimension is None:
                return False
            if other_dimension not in our_dimension:
                return False
        return True

    def contains_point(self, point):
        """ Checks if point belongs to this space.

        For a point to belong to a space:
            1. the point has to specify a coordinate for all dimensions in self.dimensions
            2. each coordinate must be contained in our dimension

        :param point:
        :return:
        """
        return all(point[dimension.name] is not None and point[dimension.name] in dimension for dimension in self._dimensions)

    def random(self, point=None):
        if point is None:
            point = Point()
        for dimension in self._dimensions:
            if dimension.name not in point:
                point[dimension.name] = dimension.random()
        return point


class CompositeHypergrid(Hypergrid):
    """ Models a hypergrid that results from joins of SimpleHypergrids and other CompositeHypergrids.

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

    def __init__(self, name, root_hypergrid, random_state=None):
        if random_state is None:
            random_state = root_hypergrid.random_state
        super(CompositeHypergrid, self).__init__(name=name, random_state=random_state)
        self.root_hypergrid = root_hypergrid

        # maps a pivot dimension name to a set of guest subgrids that are joined on that external dimension
        #
        self.guest_subgrids_by_pivot_dimension = dict()

        # maps a subgrid name to the subgrid
        #
        self.subgrids_by_name = dict()

    @property
    def random_state(self):
        return self._random_state

    @random_state.setter
    def random_state(self, value):
        self._random_state = value
        self.root_hypergrid.random_state = self.random_state
        for _, subgrid in self.subgrids_by_name.items():
            subgrid.random_state = self.random_state

    def __getitem__(self, dimension_name):
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(dimension_name)
        if subgrid_name is None:
            return self.root_hypergrid[dimension_name]
        subgrid = self.subgrids_by_name[subgrid_name]
        return subgrid[dimension_name_without_subgrid_name]


    def __str__(self):
        return f"{self.name}"

    def add_subgrid_on_external_dimension(self, other_hypergrid: Hypergrid, external_dimension: Dimension):
        assert self.root_hypergrid[external_dimension.name] is not None, f"{self.name} does not contain dimension {external_dimension.name}"
        if not self[external_dimension.name].intersects(external_dimension):
            # They don't intersect so nothing to do
            return

        guest_subgrids_joined_on_dimension = self.guest_subgrids_by_pivot_dimension.get(external_dimension.name, set())
        if any(guest_subgrid.subgrid.name == other_hypergrid.name for guest_subgrid in guest_subgrids_joined_on_dimension):
            raise RuntimeError(f"Subgrid {other_hypergrid.name} already joined to hypergrid {self.name} along the dimension {external_dimension.name}.")

        other_hypergrid.random_state = self.random_state
        guest_subgrids_joined_on_dimension.add(CompositeHypergrid.GuestSubgrid(subgrid=other_hypergrid, external_pivot_dimension=external_dimension))
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
        """ Checks if point belongs to the composite hypergrid.

        We must first see if for every dimension of the root hypergrid, the Point:
        a) specifies the dimension
        b) the value along that dimension is within bounds

        Then for every pivotal dimension present in the point we must:
        a) find the corresponding subgrid that might have been joined
        b) check if the value along pivotal dimension belongs to that subgrid
        c) if b) is true, then for every dimension in the subgrid, check if the points dimension
            values are within bounds.

        This has to be recursive, because any of the subgrids can be composite already.

        :param point:
        :return:
        """

        if point not in self.root_hypergrid:
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

    def random(self, point=None):
        if point is None:
            point = Point()
        point = self.root_hypergrid.random(point)

        for external_dimension_name, guest_subgrids_joined_on_dimension in self.guest_subgrids_by_pivot_dimension.items():
            for guest_subgrid in guest_subgrids_joined_on_dimension:
                if point[external_dimension_name] in guest_subgrid.external_pivot_dimension:
                    sub_point = guest_subgrid.subgrid.random()
                    point[guest_subgrid.subgrid.name] = sub_point

        return point

    @property
    def dimensions(self):
        for dimension in self.root_hypergrid.dimensions:
            yield dimension
        for subgrid_name, subgrid in self.subgrids_by_name.items():
            for dimension in subgrid.dimensions:
                returned_dimension = dimension.copy()
                returned_dimension.name = subgrid_name + "." + returned_dimension.name
                yield returned_dimension

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

        dimensions_by_name = {dimension.name: dimension for dimension in self.root_hypergrid.dimensions}
        ordered_dimension_names = [dimension.name for dimension in self.root_hypergrid.dimensions]

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
