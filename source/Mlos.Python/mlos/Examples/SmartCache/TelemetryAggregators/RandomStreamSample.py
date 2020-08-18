#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

class RandomStreamSample:
    """ This class represets a random sample of elements obtained from a stream of unknown length.
    """

    def __init__(self, max_sample_size, random_number_generator, max_time_horizon):
        assert max_sample_size > 0
        self._stream_length = 0
        self.max_sample_size = max_sample_size
        self.max_time_horizon = max_time_horizon
        self.elements_list = []
        self.elements_set = set()
        self.random_number_generator = random_number_generator

    def __len__(self):
        return len(self.elements_list)

    def observe(self, value):
        self._stream_length += 1

        if value in self.elements_set:
            return

        # We don't have it. Let's see if we want to keep it.
        if len(self.elements_list) <= self.max_sample_size:
            # We definitely want to keep it since we have room to keep more.
            self.elements_list.append(value)
            self.elements_set.add(value)
            return

        # We don't have it. Let's see if we want to keep it.
        probability_of_retention = min(self.max_sample_size / min(self.max_time_horizon, self._stream_length), 1)
        if self.random_number_generator.random() < probability_of_retention:
            # We do. Let's find its new home.
            index = math.floor(self.random_number_generator.random() * self.max_sample_size)
            self.elements_set.remove(self.elements_list[index])
            self.elements_list[index] = value
            self.elements_set.add(value)
        return
