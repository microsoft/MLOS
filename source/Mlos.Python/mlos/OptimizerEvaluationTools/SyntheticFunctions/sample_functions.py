#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np


def quadratic(**kwargs) -> float:
    return sum(x_i ** 2 for _, x_i in kwargs.items())

def ackley(x_1=None, x_2=None, a=20, b=0.2, c=2*math.pi):
    d = 2
    return -a * np.exp(-b * np.sqrt((x_1**2 + x_2**2) / d)) - np.exp(np.cos(c * x_1) + np.cos(c * x_2)) + a + np.exp(1)

def flower(**kwargs):
    a = 1
    b = 2
    c = 4

    x_1 = kwargs['x_1']
    x_2 = kwargs['x_2']

    x_norm = np.sqrt(x_1**2 + x_2**2)

    return a * x_norm + b * np.sin(c * np.arctan2(x_1, x_2))
