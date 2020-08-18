#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from threading import Thread
import time
from collections import namedtuple

ClockTick = namedtuple(
    typename='ClockTick',
    field_names=[
        'elapsed_time_ms'
    ]
)


class Clock:
    """ Pumps clock ticks onto the telemetry channel.

    """

    def __init__(self, communication_channel, tick_frequency_ms):
        self._communication_channel = communication_channel
        self._tick_frequency_ms = tick_frequency_ms
        self._keep_running = False
        self._clock_thread = Thread(target=self.run)

    def start(self):
        self._keep_running = True
        self._clock_thread.start()

    def run(self):
        start_time = time.time()
        while self._keep_running:
            current_time = time.time()
            elapsed_time_ms = (current_time - start_time) * 1000
            self._communication_channel.submit_message(
                ClockTick(elapsed_time_ms=elapsed_time_ms)
            )
            time.sleep(self._tick_frequency_ms / 1000.0)

    def stop(self):
        self._keep_running = False
