#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Mlos.SDK import MlosObject

class MlosRuntimeDecisionContext:
    """ An abstract class from which all runtime decision contexts inherit.

    """
    def __init__(self, mlos_object: MlosObject, timeout_ms=None):
        # keep track of the mlos_object associated with a given decision.
        self.mlos_object = mlos_object

        # If no decision from the decision maker is made, a default decision will be returned
        self._timeout_ms = timeout_ms

    @property
    def default_decision(self):
        """ A default decision to be made, in case the decision maker is unable to respond in time.

        A multitude of reasons why a decision maker might not be able to respond in time:
            1. No intelligence is actually connected to the component.
            2. Network latency / communication failure
            3. Model process crashes
            4. Model scoring is too time consuming

        This property allows us to fall back to either a constant, or a simple heuristic computed locally.
        :return:
        """

        raise NotImplementedError("Each subclass should implement this method.")
