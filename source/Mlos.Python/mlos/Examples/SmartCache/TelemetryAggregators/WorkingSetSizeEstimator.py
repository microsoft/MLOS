#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random

from mlos.Mlos.SDK import MlosTelemetryAggregator
from mlos.Examples.SmartCache.MlosInterface.MlosTelemetryMessages import SmartCacheGet
from mlos.Examples.SmartCache import SmartCache

from .RandomStreamSample import RandomStreamSample
from .WorkingSetSizeEstimate import WorkingSetSizeEstimate


class WorkingSetSizeEstimator(MlosTelemetryAggregator):
    """ Implementation of the working set size estimator.

    The idea here is pretty simple:
        1. Collect two random i.i.d. samples from the stream.
        2. Use capture-mark-recapture method to estimate the size of the population. You can do it, by observing how many
            elements are present in __both__ the random samples.

    Limitation: In all fairness, this estimator will estimate the size of the entire population of items ever present on
        this stream. In order to estimate the size of the working set, we would need to collect random samples over time,
        and measure drift. Maybe sometime later.
    """

    def __init__(self, sample_size_A=100, sample_size_B=100, seed_A=1, seed_B=2, max_time_horizon=10000):
        super(WorkingSetSizeEstimator, self).__init__()
        self.sample_size_A = sample_size_A
        self.sample_size_B = sample_size_B
        self.sample_A = RandomStreamSample(self.sample_size_A, random.Random(seed_A), max_time_horizon)
        self.sample_B = RandomStreamSample(self.sample_size_B, random.Random(seed_B), max_time_horizon)

    @MlosTelemetryAggregator.register_callback(SmartCache, SmartCacheGet)
    def observe(self, smart_cache_get_message):
        key = smart_cache_get_message.key
        self.sample_A.observe(key)
        self.sample_B.observe(key)

    def estimate_working_set_size(self):
        intersection_size = len(self.sample_A.elements_set.intersection(self.sample_B.elements_set))
        return WorkingSetSizeEstimate(len(self.sample_A), len(self.sample_B), intersection_size)
