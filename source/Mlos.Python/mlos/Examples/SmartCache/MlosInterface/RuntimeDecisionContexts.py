#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Mlos.SDK import MlosRuntimeDecisionContext

class ReconfigurationRuntimeDecisionContext(MlosRuntimeDecisionContext):

    def __init__(self, mlos_object):
        """ TODO: initialize all fields that could be useful for a runtime decision.

        """
        super(ReconfigurationRuntimeDecisionContext, self).__init__(mlos_object=mlos_object)

    @property
    def default_decision(self):
        return True


class PushRuntimeDecisionContext(MlosRuntimeDecisionContext):
    """ Context to facilitate a decision whether to push a key onto the cache or not.

    """

    def __init__(self, mlos_object, current_config):
        super(PushRuntimeDecisionContext, self).__init__(mlos_object=mlos_object)
        self.current_config = current_config

    @property
    def default_decision(self):
        return True
