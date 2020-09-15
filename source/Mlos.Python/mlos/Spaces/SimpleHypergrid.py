#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Exceptions import PointOutOfDomainException
from mlos.Spaces.Dimensions.Dimension import Dimension
from mlos.Spaces.Hypergrid import Hypergrid
from mlos.Spaces.Point import Point


class SimpleHypergrid(Hypergrid):
    """ Models a space comprized of Continuous, Discrete, Ordinal and Categorical Dimensions.

    Can be flat or hierarchical, depending if any join operations were performed.

    """
    class JoinedSubgrid:
        """ Allows a subgrid to be joined on a dimension that's not in that subgrid.

        Think how in SQL you can do:
            SELECT * FROM Employee JOIN Employer ON Employee.Name = 'John';
        The JOIN predicate does not reference any column in Employer so we end up with a cross product of all John's with
        all employers.

        That's kinda the idea here. We want to join a subgrid on an arbitrary predicate expressed by that join_dimension.
        """
        def __init__(self, subgrid, join_dimension):
            self.subgrid = subgrid
            self.join_dimension = join_dimension

        def to_string(self, indent=0):
            """ Returns it's own string representation.

            :param indent:
            :return:
            """
            indent_str = ' ' * indent
            return f"\n{indent_str}IF {self.join_dimension.name} IN {self.join_dimension.to_string(include_name=False)} THEN (" \
                   f"\n{self.subgrid.to_string(indent=indent+2)}" \
                   f"\n{indent_str})"

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
        self.joined_subgrids_by_pivot_dimension = dict()

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

    def __getitem__(self, dimension_or_subgrid_name):
        subgrid_name, name_without_subgrid_name = Dimension.split_dimension_name(dimension_or_subgrid_name)
        if subgrid_name is None:
            if name_without_subgrid_name in self.dimensions_dict.keys():
                return self.dimensions_dict[dimension_or_subgrid_name]
            if name_without_subgrid_name in self.subgrids_by_name.keys():
                return self.subgrids_by_name[name_without_subgrid_name]
            raise KeyError(f"{dimension_or_subgrid_name} does not match any dimension names nor any subgrid names.")
        subgrid = self.subgrids_by_name[subgrid_name]
        return subgrid[name_without_subgrid_name]

    def get(self, dimension_or_subgrid_name, default=None):
        try:
            return self[dimension_or_subgrid_name]
        except KeyError:
            return default

    def __repr__(self):
        return f"{self.to_string(indent=2)}"

    def to_string(self, indent=0):
        indent_str = ' ' * indent
        dimensions_indent_str = ' ' * (indent+2)
        root_grid_header = f"{indent_str}Name: {self.name}\n" \
                           f"{indent_str}Dimensions:\n"
        root_dimension_strings = []
        for dimension in self._dimensions:
            root_dimension_strings.append(f"{dimensions_indent_str}{dimension}")
        root_grid_string = root_grid_header + "\n".join(root_dimension_strings)

        if self.is_hierarchical():
            root_grid_string += "\n"

        subgrid_strings = []
        for _, joined_subgrids in self.joined_subgrids_by_pivot_dimension.items():
            for joined_subgrid in joined_subgrids:
                subgrid_strings.append(joined_subgrid.to_string(indent=indent))
        subgrid_string = "\n".join(subgrid_strings)
        return root_grid_string + subgrid_string

    def add_subgrid_on_external_dimension(self, other_hypergrid: Hypergrid, external_dimension: Dimension):
        assert external_dimension.name in self.dimensions_dict, f"{self.name} does not contain dimension {external_dimension.name}"
        assert other_hypergrid.name not in self.dimensions_dict.keys(), f"{other_hypergrid.name} collides with a dimension name."
        if not self[external_dimension.name].intersects(external_dimension):
            # They don't intersect so nothing to do
            return

        guest_subgrids_joined_on_dimension = self.joined_subgrids_by_pivot_dimension.get(external_dimension.name, set())
        if any(guest_subgrid.subgrid.name == other_hypergrid.name for guest_subgrid in guest_subgrids_joined_on_dimension):
            raise RuntimeError(f"Subgrid {other_hypergrid.name} already joined to hypergrid {self.name} along the dimension {external_dimension.name}.")

        other_hypergrid.random_state = self.random_state
        guest_subgrids_joined_on_dimension.add(SimpleHypergrid.JoinedSubgrid(subgrid=other_hypergrid, join_dimension=external_dimension))
        self.joined_subgrids_by_pivot_dimension[external_dimension.name] = guest_subgrids_joined_on_dimension
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
        if subgrid is None:
            return self
        assert on_external_dimension is not None

        if subgrid.name in self.dimensions_dict.keys():
            raise ValueError(f"{subgrid.name} collides with a dimension name.")

        external_dimension = on_external_dimension
        join_dimension_name = external_dimension.name
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(join_dimension_name)
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

        if not all(point.get(dimension.name) is not None and point.get(dimension.name) in dimension for dimension in self._dimensions):
            return False

        for external_dimension_name, guest_subgrids_joined_on_dimension in self.joined_subgrids_by_pivot_dimension.items():
            for guest_subgrid in guest_subgrids_joined_on_dimension:
                if point[external_dimension_name] in guest_subgrid.join_dimension:
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

        for external_dimension_name, guest_subgrids_joined_on_dimension in self.joined_subgrids_by_pivot_dimension.items():
            for joined_subgrid in guest_subgrids_joined_on_dimension:
                if point[external_dimension_name] in joined_subgrid.join_dimension:
                    sub_point = joined_subgrid.subgrid.random()
                    point[joined_subgrid.subgrid.name] = sub_point

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

    def get_dimensions_for_point(self, point, return_join_dimensions=True):
        """ Returns dimensions that the given point belongs to.

        For join dimensions, it can return the joined_subgrid.join_dimension if return_join_dimensions == True,
        else it returns the original dimension.

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

        for external_dimension_name, guest_subgrids_joined_on_dimension in self.joined_subgrids_by_pivot_dimension.items():
            for joined_subgrid in guest_subgrids_joined_on_dimension:
                if point[external_dimension_name] in joined_subgrid.join_dimension:
                    # We return this narrower join dimension, since point[join_dimension_name] has
                    # to belong to the join_dimension for all of the subgrid dimensions to make sense.
                    #
                    if return_join_dimensions:
                        dimensions_by_name[external_dimension_name] = joined_subgrid.join_dimension
                    subgrid = joined_subgrid.subgrid
                    for dimension in subgrid.get_dimensions_for_point(point[subgrid.name], return_join_dimensions=return_join_dimensions):
                        dimension = dimension.copy()
                        dimension.name = f"{subgrid.name}.{dimension.name}"
                        dimensions_by_name[dimension.name] = dimension
                        ordered_dimension_names.append(dimension.name)

        # Returning dimensions in order they were visited (mostly to make sure that root dimension names come first.
        #
        return [dimensions_by_name[name] for name in ordered_dimension_names]
