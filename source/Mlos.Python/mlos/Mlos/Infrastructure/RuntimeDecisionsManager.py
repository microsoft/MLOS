#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class RuntimeDecisionsManager:
    """ Binds decision makers with decision seekers.

    The job of the RuntimeDecisionManager is to:
    1. Allow smart components to request runtime decisions.
    2. Forwarding those decision requests to the appropriate decision maker:
        * constant
        * heuristic
        * trained model
        * RL
    3. Forwarding decisions from the decision maker back to the smart component.

    In practice, it's conceivable that we will just bind the "mlosObject.RuntimeDecision()" function
    to the function we want to invoke.

    """

    def __init__(self):
        self._runtime_decision_makers = dict()

    def add_runtime_decision_maker(self, runtime_decision_maker):
        runtime_decision_context_type = runtime_decision_maker.decision_context_type
        self._runtime_decision_makers[runtime_decision_context_type] = runtime_decision_maker

    def remove_runtime_decision_maker(self, runtime_decision_maker):
        runtime_decision_context_type = runtime_decision_maker.decision_context_type
        if runtime_decision_context_type in self._runtime_decision_makers:
            del self._runtime_decision_makers[runtime_decision_context_type]



    def make_runtime_decision(self, mlos_object, runtime_decision_context):
        """ Makes a runtime decision based on the decision context.

        If there is a decision maker registered for a given decision (as defined by any active
        experiment), then the context, along with component type and runtime attributes is
        forwarded to the MlosAgent. Otherwise the default decision is returned.

        :param runtime_decision_context:
        :return:
        """

        runtime_decision_maker = self._runtime_decision_makers.get(type(runtime_decision_context), None)

        if runtime_decision_maker is not None:
            return runtime_decision_maker(runtime_decision_context, mlos_object)

        return runtime_decision_context.default_decision
