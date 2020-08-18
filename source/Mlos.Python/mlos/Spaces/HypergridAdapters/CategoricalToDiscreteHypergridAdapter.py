#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from pandas import DataFrame
from mlos.Spaces import CategoricalDimension, DiscreteDimension, Hypergrid, Point, SimpleHypergrid, CompositeHypergrid
from mlos.Spaces.HypergridAdapters.HypergridAdapter import HypergridAdapter

class CategoricalToDiscreteHypergridAdapter(HypergridAdapter):
    """ Maps values in categorical dimensions into values in discrete dimensions.

    """

    def __init__(self, adaptee: Hypergrid):
        HypergridAdapter.__init__(self, name=adaptee.name, random_state=adaptee.random_state)
        self._adaptee: Hypergrid = adaptee
        self._target: Hypergrid = None

        # Forward mapping:
        #   Key: dimension name
        #   Value: a dictionary mapping adaptee values to target values
        #
        self._adaptee_to_target_dimension_mappings = dict()

        # Reverse mapping:
        #   Key: dimension name
        #   Value: a dictionary mapping target values to adaptee values
        self._target_to_adaptee_dimension_mappings = dict()


        # Now we need to build the target hypergrid and the mappings between adaptee and target.
        if isinstance(adaptee, SimpleHypergrid) or (isinstance(adaptee, HypergridAdapter) and isinstance(adaptee.target, SimpleHypergrid)):
            self._build_simple_hypergrid_target()
        elif isinstance(adaptee, CompositeHypergrid) or (isinstance(adaptee, HypergridAdapter) and isinstance(adaptee.target, CompositeHypergrid)):
            self._build_composite_hypergrid_target()

    @property
    def adaptee(self) -> Hypergrid:
        return self._adaptee

    @property
    def target(self) -> Hypergrid:
        return self._target

    def _translate_point(self, point: Point) -> Point:
        translated_point = Point()
        for dim_name, original_dim_value in point:
            forward_mapping = self._adaptee_to_target_dimension_mappings.get(dim_name, None)
            if forward_mapping is None:
                translated_point[dim_name] = original_dim_value
            else:
                translated_point[dim_name] = forward_mapping[original_dim_value]
        return translated_point

    def _untranslate_point(self, point: Point) -> Point:
        untranslated_point = Point()
        for dim_name, translated_dim_value in point:
            backward_mapping = self._target_to_adaptee_dimension_mappings.get(dim_name, None)
            if backward_mapping is None:
                untranslated_point[dim_name] = translated_dim_value
            else:
                untranslated_point[dim_name] = backward_mapping[translated_dim_value]
        return untranslated_point

    def _translate_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        # For each dimension that has a forward mapping, apply the mapping to the corresponding column.
        #
        if not in_place:
            df = df.copy(deep=True)
        for dim_name, forward_mapping in self._adaptee_to_target_dimension_mappings.items():
            df[dim_name] = df[dim_name].apply(lambda original_value: forward_mapping.get(original_value, original_value))  # pylint: disable=cell-var-from-loop
        return df

    def _untranslate_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)
        for dim_name, backward_mapping in self._target_to_adaptee_dimension_mappings.items():
            df[dim_name] = df[dim_name].apply(lambda original_value: backward_mapping.get(original_value, original_value))  # pylint: disable=cell-var-from-loop
        return df

    def _build_simple_hypergrid_target(self) -> None:
        """ Builds a SimpleHypergrid target for a SimpleHypergrid adaptee.

        :return:
        """
        assert isinstance(self.adaptee, SimpleHypergrid) or \
               (isinstance(self.adaptee, HypergridAdapter) and isinstance(self.adaptee.target, SimpleHypergrid))

        self._target = SimpleHypergrid(
            name=self._adaptee.name,
            dimensions=None,
            random_state=self._adaptee.random_state
        )

        # Now we iterate over all dimensions and when necessary map the CategoricalDimensions to DiscreteDimensions
        #
        for adaptee_dimension in self._adaptee.dimensions:
            if not isinstance(adaptee_dimension, CategoricalDimension):
                self._target.add_dimension(adaptee_dimension.copy())
            else:
                target_dimension = self._map_categorical_dimension(adaptee_dimension)
                self._target.add_dimension(target_dimension)

    def _map_categorical_dimension(self, adaptee_dimension: CategoricalDimension) -> DiscreteDimension:
        """ Translates a categorical dimension into a discrete dimension and persists the mappings.

        :param adaptee_dimension:
        :return:
        """
        forward_mapping = {}
        backward_mapping = {}
        for i, value in enumerate(adaptee_dimension):
            forward_mapping[value] = i
            backward_mapping[i] = value

        self._adaptee_to_target_dimension_mappings[adaptee_dimension.name] = forward_mapping
        self._target_to_adaptee_dimension_mappings[adaptee_dimension.name] = backward_mapping
        target_dimension = DiscreteDimension(
            name=adaptee_dimension.name,
            min=0,
            max=len(adaptee_dimension) - 1
        )
        return target_dimension


    def _build_composite_hypergrid_target(self) -> None:
        """ Not implemented.

        I gave implementing this several tries and I want to capture my learning here for posterity (and my future self).

        So the two approaches I have taken were:

        ####################################################################################################################
        Approach 1:
        Keep all the logic here - this means look at the Composite Hypergrid, and by inspecting it public state,
        reconstruct a slightly altered copy with all CategoricalDimensions and OrdinalDimensions replaced with
        DiscreteDimensions.

        This has several weaknesses:
            1. We really depend on that CompositeHypergrid API to remain very stable and we essentially add inertia
                to the CompositeHypergrid class.
            2. It's complex. Each CompositeHypergrid can have Hypergrids joined on dimension and on external dimension,
                and it's quite tricky (though obviously possible) to do it.

        ####################################################################################################################
        Approach 2:
        Add two methods to the Hypergrid API: copy(), and replace_dimension(...).

        This has even more weaknesses:
            1. The CompositeHypergrid class becomes bloated. While the .copy() API might be generally useful, the
                replace_dimension(...) API is super specific to this adapter.
            2. Again, any changes to the CompositeHypergrid class now require changing 2 more, recursive methods.
            3. The replace_dimension(...) method is so specific to this adapter and requires keeping so much
                state that it actually hurts to see it in the CompositeHypergrid class.
        ####################################################################################################################

        Having explored the two options above I turned to the "Zen of Python" and Greg.

        Greg recommended a visitor pattern with many advantages:
            1. It decouples the innards of CompositeHypergrdis from anything operating on it.
            2. There is already a bunch of recursive algorithms applied over CompositeHypergrids and if we expect many
                more than the Adapter Patter is probably the way to go.

        But... This functionality is not urgent so we can spend some time designing it properly and we can come back to
        it when we need to.

        Three or four lines from the "Zen of Python" pertain:

            Simple is better than complex.
            Complex is better than complicated.
            Flat is better than nested.
            ...
            There should be one-- and preferably only one --obvious way to do it.

            So in the name of simply-flat I believe that the only HypergridAdapter for Composite Hypergrids we need
        right now is a CompositeHypergridToSimpleHypergrid flattening adapter that flattens the hierarchy. All of the
        other adapters can be stacked on top of it. It solves our immediate problem without compromise, because we
        have to apply the flattening adapter anyway before sending the data to the models.

        :return:
        """
        assert isinstance(self.adaptee, CompositeHypergrid) or \
               (isinstance(self.adaptee, HypergridAdapter) and isinstance(self.adaptee.target, CompositeHypergrid))
        raise NotImplementedError
