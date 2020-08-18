#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
from scipy.stats import norm


class WorkingSetSizeEstimate:
    def __init__(self, sample_size_A, sample_size_B, intersection_size):
        self.sample_size_A = sample_size_A
        self.sample_size_B = sample_size_B
        self.intersection_size = intersection_size

    @property
    def lincoln_petersen_estimator(self):
        return 1.0 * self.sample_size_A * self.sample_size_B / self.intersection_size

    @property
    def chapman_estimator(self):
        return math.floor(1.0 * (self.sample_size_A + 1) * (self.sample_size_B + 1) / (self.intersection_size + 1))

    def confidence_interval(self, alpha):
        """ As detailed here: https://www.webpages.uidaho.edu/wlf448/cap_recap.htm

        """
        z_score = norm.ppf(1 - alpha / 2)
        variance = (
            (self.sample_size_A + 1) *
            (self.sample_size_B + 1) *
            (self.sample_size_A - self.intersection_size) *
            (self.sample_size_B - self.intersection_size)
            ) / ((self.intersection_size + 1) ** 2 * (self.intersection_size + 2))

        error_margin = z_score * math.sqrt(variance)
        center = self.chapman_estimator
        return center - error_margin, center + error_margin
