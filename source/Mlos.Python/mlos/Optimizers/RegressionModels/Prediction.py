#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

class Prediction:
    """ Represents a prediction made by a model.

    It encapsulates mean and variance and will have convenience methods to compute
    confidence intervals, etc.

    # TODO: this whole class is dumb. Use a pandas dataframe instead.

    """

    def __init__(self, target_name, mean=0, variance=math.inf, count=0, standard_deviation=None, valid=True):
        self.target_name = target_name
        self.mean = mean
        self.variance = variance
        self.standard_deviation = math.sqrt(variance) if standard_deviation is None else standard_deviation
        self.count = count
        self.valid = valid

    def __str__(self):
        return f"mean: {self.mean}, variance: {self.variance}, count: {self.count}"
