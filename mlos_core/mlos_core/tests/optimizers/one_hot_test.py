#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for one-hot encoding for certain optimizers.
"""

import pytest

import pandas as pd
import numpy as np
import numpy.typing as npt
import ConfigSpace as CS

from mlos_core.optimizers import EmukitOptimizer

# pylint: disable=protected-access,redefined-outer-name


@pytest.fixture
def data_frame() -> pd.DataFrame:
    """
    Toy data frame corresponding to the `configuration_space` hyperparameters.
    The columns are deliberately *not* in alphabetic order.
    """
    return pd.DataFrame({
        'y': ['a', 'b', 'c'],
        'x': [0.1, 0.2, 0.3],
        'z': [1, 5, 8],
    })


@pytest.fixture
def one_hot() -> npt.NDArray:
    """
    One-hot encoding of the `data_frame` above.
    The columns follow the order of the hyperparameters in `configuration_space`.
    """
    return np.array([
        [0.1, 1.0, 0.0, 0.0, 1.0],
        [0.2, 0.0, 1.0, 0.0, 5.0],
        [0.3, 0.0, 0.0, 1.0, 8.0],
    ])


def test_to_1hot(configuration_space: CS.ConfigurationSpace,
                 data_frame: pd.DataFrame, one_hot: npt.NDArray):
    """
    Toy problem to test one-hot encoding.
    """
    optimizer = EmukitOptimizer(configuration_space)
    assert optimizer._to_1hot(data_frame) == pytest.approx(one_hot)


def test_from_1hot(configuration_space: CS.ConfigurationSpace,
                   data_frame: pd.DataFrame, one_hot: npt.NDArray):
    """
    Toy problem to test one-hot decoding.
    """
    optimizer = EmukitOptimizer(configuration_space)
    assert optimizer._from_1hot(one_hot).to_dict() == data_frame.to_dict()


def test_round_trip(configuration_space: CS.ConfigurationSpace, data_frame: pd.DataFrame):
    """
    Round-trip test for one-hot-encoding and then decoding a data frame.
    """
    optimizer = EmukitOptimizer(configuration_space)
    df_round_trip = optimizer._from_1hot(optimizer._to_1hot(data_frame))
    assert df_round_trip.x.to_numpy() == pytest.approx(data_frame.x)
    assert (df_round_trip.y == data_frame.y).all()
    assert (df_round_trip.z == data_frame.z).all()


def test_round_trip_reverse(configuration_space: CS.ConfigurationSpace, one_hot: npt.NDArray):
    """
    Round-trip test for one-hot-decoding and then encoding of a numpy array.
    """
    optimizer = EmukitOptimizer(configuration_space)
    round_trip = optimizer._to_1hot(optimizer._from_1hot(one_hot))
    assert round_trip == pytest.approx(one_hot)
