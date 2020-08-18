#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Mlos.SDK import MlosTelemetryAggregator
from mlos.Mlos.SDK.Utils.Clock import Clock, ClockTick

class Timer(MlosTelemetryAggregator):
    """ An aggregator that responds to clock ticks.

    The idea is that when a timer runs out, it invokes its observer and
    then restarts itself.
    """

    def __init__(self, timeout_ms, observer_callback, epsilon_ms=10):
        super(Timer, self).__init__()
        self.timeout_ms = timeout_ms
        self.epsilon_ms = epsilon_ms
        self.observer_callback = observer_callback
        self.start = None

    @MlosTelemetryAggregator.register_callback(Clock, ClockTick)
    def observe_clock_tick(self, clock_tick_message):
        if self.start is None:
            self.start = clock_tick_message.elapsed_time_ms

        elapsed_time = clock_tick_message.elapsed_time_ms - self.start
        if elapsed_time + self.epsilon_ms > self.timeout_ms:
            self.start = clock_tick_message.elapsed_time_ms
            self.observer_callback(elapsed_time)
