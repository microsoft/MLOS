#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Mlos.SDK import MlosTelemetryAggregator
from mlos.Examples.SmartCache.MlosInterface.MlosTelemetryMessages import SmartCacheGet
from mlos.Examples.SmartCache import SmartCache


class HitRateMonitor(MlosTelemetryAggregator):
    """ Gathers statistics about the miss/hit rates of the SmartCache.

    """
    def __init__(self):
        MlosTelemetryAggregator.__init__(self)
        self.num_requests = 0
        self._num_hits = 0

    def reset(self):
        self.num_requests = 0
        self._num_hits = 0

    @MlosTelemetryAggregator.register_callback(component_type=SmartCache, message_type=SmartCacheGet)
    def observe(self, smart_cache_get_message):
        self.num_requests += 1
        if smart_cache_get_message.was_hit:
            self._num_hits += 1

    def get_hit_rate(self):
        return (1.0 * self._num_hits + 0.000001) / (self.num_requests + 0.000001)

    def get_miss_rate(self):
        return 1 - self.get_hit_rate()
