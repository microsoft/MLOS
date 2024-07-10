#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for one-hot encoding for certain optimizers."""

import ConfigSpace as CS
import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest

from mlos_core.optimizers import BaseOptimizer, SmacOptimizer

# pylint: disable=protected-access,redefined-outer-name


@pytest.fixture
def data_frame() -> pd.DataFrame:
    """
    Toy data frame corresponding to the `configuration_space` hyperparameters.

    The columns are deliberately *not* in alphabetic order.
    """
    return pd.DataFrame(
        {
            "y": ["a", "b", "c"],
            "x": [0.1, 0.2, 0.3],
            "z": [1, 5, 8],
        }
    )


@pytest.fixture
def one_hot_data_frame() -> npt.NDArray:
    """
    One-hot encoding of the `data_frame` above.

    The columns follow the order of the hyperparameters in `configuration_space`.
    """
    return np.array(
        [
            [0.1, 1.0, 0.0, 0.0, 1.0],
            [0.2, 0.0, 1.0, 0.0, 5.0],
            [0.3, 0.0, 0.0, 1.0, 8.0],
        ]
    )


@pytest.fixture
def series() -> pd.Series:
    """
    Toy series corresponding to the `configuration_space` hyperparameters.

    The columns are deliberately *not* in alphabetic order.
    """
    return pd.Series(
        {
            "y": "b",
            "x": 0.4,
            "z": 3,
        }
    )


@pytest.fixture
def one_hot_series() -> npt.NDArray:
    """
    One-hot encoding of the `series` above.

    The columns follow the order of the hyperparameters in `configuration_space`.
    """
    return np.array(
        [
            [0.4, 0.0, 1.0, 0.0, 3],
        ]
    )


@pytest.fixture
def optimizer(configuration_space: CS.ConfigurationSpace) -> BaseOptimizer:
    """
    Test fixture for the optimizer.

    Use it to test one-hot encoding/decoding.
    """
    return SmacOptimizer(
        parameter_space=configuration_space,
        optimization_targets=["score"],
    )


def test_to_1hot_data_frame(
    optimizer: BaseOptimizer,
    data_frame: pd.DataFrame,
    one_hot_data_frame: npt.NDArray,
) -> None:
    """Toy problem to test one-hot encoding of dataframe."""
    assert optimizer._to_1hot(config=data_frame) == pytest.approx(one_hot_data_frame)


def test_to_1hot_series(
    optimizer: BaseOptimizer,
    series: pd.Series,
    one_hot_series: npt.NDArray,
) -> None:
    """Toy problem to test one-hot encoding of series."""
    assert optimizer._to_1hot(config=series) == pytest.approx(one_hot_series)


def test_from_1hot_data_frame(
    optimizer: BaseOptimizer,
    data_frame: pd.DataFrame,
    one_hot_data_frame: npt.NDArray,
) -> None:
    """Toy problem to test one-hot decoding of dataframe."""
    assert optimizer._from_1hot(config=one_hot_data_frame).to_dict() == data_frame.to_dict()


def test_from_1hot_series(
    optimizer: BaseOptimizer,
    series: pd.Series,
    one_hot_series: npt.NDArray,
) -> None:
    """Toy problem to test one-hot decoding of series."""
    one_hot_df = optimizer._from_1hot(config=one_hot_series)
    assert one_hot_df.shape[0] == 1, f"Unexpected number of rows ({one_hot_df.shape[0]} != 1)"
    assert one_hot_df.iloc[0].to_dict() == series.to_dict()


def test_round_trip_data_frame(optimizer: BaseOptimizer, data_frame: pd.DataFrame) -> None:
    """Round-trip test for one-hot-encoding and then decoding a data frame."""
    df_round_trip = optimizer._from_1hot(config=optimizer._to_1hot(config=data_frame))
    assert df_round_trip.x.to_numpy() == pytest.approx(data_frame.x)
    assert (df_round_trip.y == data_frame.y).all()
    assert (df_round_trip.z == data_frame.z).all()


def test_round_trip_series(optimizer: BaseOptimizer, series: pd.DataFrame) -> None:
    """Round-trip test for one-hot-encoding and then decoding a series."""
    series_round_trip = optimizer._from_1hot(config=optimizer._to_1hot(config=series))
    assert series_round_trip.x.to_numpy() == pytest.approx(series.x)
    assert (series_round_trip.y == series.y).all()
    assert (series_round_trip.z == series.z).all()


def test_round_trip_reverse_data_frame(
    optimizer: BaseOptimizer,
    one_hot_data_frame: npt.NDArray,
) -> None:
    """Round-trip test for one-hot-decoding and then encoding of a numpy array."""
    round_trip = optimizer._to_1hot(config=optimizer._from_1hot(config=one_hot_data_frame))
    assert round_trip == pytest.approx(one_hot_data_frame)


def test_round_trip_reverse_series(optimizer: BaseOptimizer, one_hot_series: npt.NDArray) -> None:
    """Round-trip test for one-hot-decoding and then encoding of a numpy array."""
    round_trip = optimizer._to_1hot(config=optimizer._from_1hot(config=one_hot_series))
    assert round_trip == pytest.approx(one_hot_series)
