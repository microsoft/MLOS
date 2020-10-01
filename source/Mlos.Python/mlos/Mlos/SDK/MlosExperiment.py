#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum


class MlosExperiment:
    """A container for all resources associated with a given experiment.

    TelemetryAggregators's resources include:
    * SmartComponent types governed by the experiment
    * SmartComponent runtime attributes set governed by the experiment
    * Telemetry enabled by the experiment
    * Decision Makers associated with each runtime decision

    The idea is that upon authoring an experiment, we pass it as an argument to the MlosAgent,
    who in turn enables all required telemetry, associates callbacks with each telemetry event
    binds decision makers to runtime decisions etc.

    Whenever an experiment completes, the MlosAgent unbinds decision makers, disables the telemetry,
    and releases the SmartComponents.

    For now we will only enable a single experiment at a time.

    Further, for now we will coarsely group SmartComponents by type, and ignore runtime attribute filters.

    Parameters
    ----------
    smart_component_types : list or None
        List of smart components to configure during experiment.

    telemetry_aggregators : list or None
        Telemetry aggregators to monitor.

    runtime_decision_makers : list or None
    """

    class Status(Enum):
        REQUESTED = 1
        BEING_INITIALIZED = 2
        IN_PROGRESS = 3
        BEING_FINALIZED = 4
        COMPLETE = 5
        FAILED = 6
        CANCELLED = 7

    def __init__(
            self,
            smart_component_types=None,
            telemetry_aggregators=None,
            runtime_decision_makers=None
    ):
        """

        :param smart_component_types: a list of SmartComponentSelectors to select components to participate in the experiment
        :param telemetry_aggregators: a list of telemetry aggregators to register as callbacks for their requested telemetry events
        :param runtime_decision_makers: a list of runtime decision makers to bind to their respective runtime decisions
        """
        self.id = None
        self.status = self.Status.REQUESTED

        if smart_component_types is None:
            smart_component_types = []
        self.smart_component_types = set(smart_component_types)

        if telemetry_aggregators is None:
            telemetry_aggregators = []
        self.telemetry_aggregators = telemetry_aggregators

        if runtime_decision_makers is None:
            runtime_decision_makers = []
        self.runtime_decision_makers = runtime_decision_makers

    @property
    def requested_message_types(self):
        message_types = set()
        for aggregator in self.telemetry_aggregators:
            message_types = message_types.union(aggregator.requested_message_types)
        return message_types
