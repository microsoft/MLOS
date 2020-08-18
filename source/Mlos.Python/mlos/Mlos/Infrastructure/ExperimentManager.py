#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Mlos.SDK.MlosExperiment import MlosExperiment
from mlos.Mlos.SDK.MlosTelemetryAggregator import MlosTelemetryAggregator


class ExperimentManager:
    """ Keeps track of all experiments currently underway by the Mlos Agent.


    """

    _next_experiment_id = 0

    def __init__(self, mlos_agent, communication_channel, logger):
        self._mlos_agent = mlos_agent
        self._communication_channel = communication_channel
        self.logger = logger

        self._active_experiments = dict()
        self._currently_targeted_component_types = set()


    @classmethod
    def _get_next_experiment_id(cls):
        cls._next_experiment_id += 1
        return cls._next_experiment_id

    def start_experiment(self, mlos_experiment):
        """
        1. Validate that the components that this experiment targets are not already targeted.

        :param mlos_experiment:
        :return:
        """
        self._assert_no_component_conflicts(mlos_experiment)

        mlos_experiment.id = self._get_next_experiment_id()
        self.logger.info(f"Starting experiment {mlos_experiment.id}")
        self._active_experiments[mlos_experiment.id] = mlos_experiment
        mlos_experiment.status = MlosExperiment.Status.BEING_INITIALIZED
        self._currently_targeted_component_types = self._currently_targeted_component_types.union(mlos_experiment.smart_component_types)
        self._enable_telemetry_and_register_callbacks(mlos_experiment)
        self._bind_runtime_decision_makers(mlos_experiment)
        mlos_experiment.status = MlosExperiment.Status.IN_PROGRESS

    def stop_experiment(self, mlos_experiment):
        mlos_experiment.status = MlosExperiment.Status.BEING_FINALIZED
        self._unbind_runtime_decision_makers(mlos_experiment)
        self._disable_telemetry_and_unregister_callbacks(mlos_experiment)
        self._currently_targeted_component_types = self._currently_targeted_component_types - mlos_experiment.smart_component_types
        mlos_experiment.status = MlosExperiment.Status.COMPLETE
        del self._active_experiments[mlos_experiment.id]
        self.logger.info(f"Stopped experiment {mlos_experiment.id}")

    def _assert_no_component_conflicts(self, mlos_experiment):
        conflicting_component_types = self._currently_targeted_component_types.intersection(mlos_experiment.smart_component_types)
        if conflicting_component_types:
            mlos_experiment.status = MlosExperiment.Status.FAILED
            raise RuntimeError(
                f"Unable to start experiment, since the following components are already being targeted by exising experiments: "
                f"{', '.join([type.__name__ for type in conflicting_component_types])}"
            )

    def _enable_telemetry_and_register_callbacks(self, mlos_experiment):
        for telemetry_aggregator in mlos_experiment.telemetry_aggregators:
            assert isinstance(telemetry_aggregator, MlosTelemetryAggregator)
            for (component_type, message_type), callback_methods in telemetry_aggregator.callbacks.items():
                self._mlos_agent.enable_telemetry_message_types(component_type, [message_type]) # TODO: aggregate...
                for callback_method in callback_methods:
                    self._mlos_agent.register_callback(message_type, callback_method)

    def _disable_telemetry_and_unregister_callbacks(self, mlos_experiment):
        assert mlos_experiment.status == MlosExperiment.Status.BEING_FINALIZED

        for telemetry_aggregator in mlos_experiment.telemetry_aggregators:
            for (component_type, message_type), callback_methods in telemetry_aggregator.callbacks.items():
                self._mlos_agent.disable_telemetry_message_types(component_type, [message_type])

                for callback_method in callback_methods:
                    self._mlos_agent.unregister_callback(message_type, callback_method)

    def _bind_runtime_decision_makers(self, mlos_experiment):
        for runtime_decision_maker in mlos_experiment.runtime_decision_makers:
            self._mlos_agent.add_runtime_decision_maker(runtime_decision_maker)

    def _unbind_runtime_decision_makers(self, mlos_experiment):
        for runtime_decision_maker in mlos_experiment.runtime_decision_makers:
            self._mlos_agent.remove_runtime_decision_maker(runtime_decision_maker)
