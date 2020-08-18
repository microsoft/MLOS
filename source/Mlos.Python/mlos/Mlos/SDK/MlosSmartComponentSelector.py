#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import Point, SimpleHypergrid


class MlosSmartComponentSelector:
    """ Selects smart components of a given type, with selected runtime attributes.

    """

    def __init__(self, smart_component_type, runtime_attributes_set: SimpleHypergrid = None):
        self.smart_component_type = smart_component_type
        self.runtime_attributes_set = runtime_attributes_set

    def __call__(self, smart_component_type, runtime_attributes):
        if self.smart_component_type != smart_component_type:
            return False
        if self.runtime_attributes_set is not None:
            # Let's check if the runtime attributes are within our set
            return Point(**runtime_attributes._asdict()) in self.runtime_attributes_set
        return True

    def __eq__(self, other):
        if not isinstance(other, MlosSmartComponentSelector):
            return False
        return (self.smart_component_type == other.smart_component_type) \
               and \
               (self.runtime_attributes_set == other.runtime_attributes_set)

    def conflicts(self, other_selector):
        """ Used to establish whether there exists a component potentially selectable by both self and other_selector

        :param other_selector:
        :return:
        """
        if self.smart_component_type != other_selector.smart_component_type:
            return False

        # Same type... Let's see if runtime_attributes_set overlaps
        if self.runtime_attributes_set is None or other_selector.runtime_attributes_set is None:
            # Either we accept everything or they do...
            return True

        # OK, the only way we do not conflict is if there is no intersection between the attribute sets
        return self.runtime_attributes_set.intersects(other_selector.runtime_attributes_set)
