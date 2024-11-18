#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for Observation Data Class."""

from typing import Optional
import pandas as pd
import pytest
import ConfigSpace as CS
from mlos_core.mlos_core.data_classes.observation import Observation
from mlos_core.mlos_core.data_classes.observations import Observations

from mlos_core.mlos_core.data_classes.suggestion import Suggestion


@pytest.fixture
def config() -> pd.Series:
    """
    Toy configuration used to build various data classes.
    """
    return pd.Series(
        {
            "y": "b",
            "x": 0.4,
            "z": 3,
        }
    )


@pytest.fixture
def score() -> pd.Series:
    """
    Toy score used for tests.
    """
    return pd.Series(
        {
            "main_score": 0.1,
            "other_score": 0.2,
        }
    )


@pytest.fixture
def metadata() -> Optional[pd.Series]:
    """
    Toy metadata used for tests.
    """
    return pd.Series(
        {
            "metadata": "test",
        }
    )


@pytest.fixture
def context() -> Optional[pd.Series]:
    """
    Toy context used for tests.
    """
    return pd.Series(
        {
            "context": "test",
        }
    )


@pytest.fixture
def config2() -> pd.Series:
    """
    An alternative toy configuration used to build various data classes.
    """
    return pd.Series(
        {
            "y": "c",
            "x": 0.7,
            "z": 1,
        }
    )


@pytest.fixture
def observation_with_context(
    config: pd.Series,
    score: pd.Series,
    metadata: Optional[pd.Series],
    context: Optional[pd.Series],
) -> Observation:
    """
    Toy observation used for tests.
    """
    return Observation(
        config=config,
        score=score,
        metadata=metadata,
        context=context,
    )


@pytest.fixture
def observation_without_context(
    config2: pd.Series,
    score2: pd.Series,
) -> Observation:
    """
    Toy observation used for tests.
    """
    return Observation(
        config=config,
        score=score,
    )


@pytest.fixture
def observations_with_context(
    config: pd.Series,
    score: pd.Series,
    metadata: Optional[pd.Series],
    context: Optional[pd.Series],
) -> Observations:
    """
    Toy observation used for tests.
    """
    observation1 = Observation(
        config=config,
        score=score,
        metadata=metadata,
        context=context,
    )
    return Observations(observations=[observation1, observation1, observation1])


@pytest.fixture
def suggestion_with_context(
    config: pd.Series,
    metadata: Optional[pd.Series],
    context: Optional[pd.Series],
) -> Observation:
    """
    Toy suggestion used for tests.
    """
    return Suggestion(
        config=config,
        metadata=metadata,
        context=context,
    )


@pytest.fixture
def suggestion_without_context(
    config2: pd.Series,
) -> Observation:
    """
    Toy suggestion used for tests.
    """
    return Suggestion(
        config=config2,
    )


def test_observation_to_suggestion(
    observation_with_context: Observation,
    observation_without_context: Observation,
) -> None:
    """Toy problem to test one-hot encoding of dataframe."""
    for observation in [observation_with_context, observation_without_context]:
        suggestion = observation.to_suggestion()
        assert suggestion._config == observation._config
        assert suggestion._context == observation._context
        assert suggestion._metadata == observation._metadata


def test_observation_equality_operators(
    observation_with_context: Observation, observation_without_context: Observation
) -> None:
    """
    Test equality operators.
    """
    assert observation_with_context == observation_with_context
    assert observation_with_context != observation_without_context
    assert observation_without_context == observation_without_context


def test_observations_init_components(
    config: pd.Series,
    score: pd.Series,
    metadata: Optional[pd.Series],
    context: Optional[pd.Series],
) -> None:
    """
    Test Observations class.
    """
    Observations(
        config=pd.concat[config.to_frame().T, config.to_frame().T],
        score=pd.concat[score.to_frame().T, score.to_frame().T],
        metadata=pd.concat[metadata.to_frame().T, metadata.to_frame().T],
        context=pd.concat[context.to_frame().T, context.to_frame().T],
    )


def test_observations_init_observations(
    observation_with_context: Observation,
) -> None:
    """
    Test Observations class.
    """
    Observations(
        observations=[observation_with_context, observation_with_context],
    )


def test_observations_init_components_fails(
    config: pd.Series,
    score: pd.Series,
    metadata: Optional[pd.Series],
    context: Optional[pd.Series],
) -> None:
    """
    Test Observations class.
    """
    with pytest.raises(AssertionError):
        Observations(
            config=pd.concat[config.to_frame().T],
            score=pd.concat[score.to_frame().T, score.to_frame().T],
            metadata=pd.concat[metadata.to_frame().T, metadata.to_frame().T],
            context=pd.concat[context.to_frame().T, context.to_frame().T],
        )
    with pytest.raises(AssertionError):
        Observations(
            config=pd.concat[config.to_frame().T, config.to_frame().T],
            score=pd.concat[score.to_frame().T],
            metadata=pd.concat[metadata.to_frame().T, metadata.to_frame().T],
            context=pd.concat[context.to_frame().T, context.to_frame().T],
        )
    with pytest.raises(AssertionError):
        Observations(
            config=pd.concat[config.to_frame().T, config.to_frame().T],
            score=pd.concat[score.to_frame().T, score.to_frame().T],
            metadata=pd.concat[metadata.to_frame().T],
            context=pd.concat[context.to_frame().T, context.to_frame().T],
        )
    with pytest.raises(AssertionError):
        Observations(
            config=pd.concat[config.to_frame().T, config.to_frame().T],
            score=pd.concat[score.to_frame().T, score.to_frame().T],
            metadata=pd.concat[metadata.to_frame().T, metadata.to_frame().T],
            context=pd.concat[context.to_frame().T],
        )


def test_observations_append(
    observation_with_context: Observation,
) -> None:
    """
    Test Observations class.
    """
    observations = Observations()
    observations.append(observation_with_context)
    observations.append(observation_with_context)
    assert len(observations) == 2


def test_observations_append_fails(
    observation_with_context: Observation,
    observation_without_context: Observation,
) -> None:
    """
    Test Observations class.
    """
    observations = Observations()
    observations.append(observation_with_context)
    with pytest.raises(AssertionError):
        observations.append(observation_without_context)


def test_observations_filter_by_index(
    observations_with_context: Observations,
) -> None:
    """
    Test Observations class.
    """
    assert len(observations_with_context.filter_by_index([0])) == 1


def test_observations_to_list(
    observations_with_context: Observations,
) -> None:
    """
    Test Observations class.
    """
    assert len(observations_with_context.to_list()) == 3
    assert all(
        isinstance(observation, Observation) for observation in observations_with_context.to_list()
    )


def test_observations_equality_test(
    observations_with_context: Observations, observations_without_context: Observations
):
    """
    Test Equality of observations.
    """
    assert observations_with_context == observations_with_context
    assert observations_with_context != observations_without_context
    assert observations_without_context == observations_without_context


def test_suggestion_equality_test(
    suggestion_with_context: Suggestion, suggestion_without_context: Suggestion
):
    """
    Test Equality of suggestions.
    """
    assert suggestion_with_context == suggestion_with_context
    assert suggestion_with_context != suggestion_without_context
    assert suggestion_without_context == suggestion_without_context


def test_complete_suggestion(
    suggestion_with_context: Suggestion, score: pd.Series, observation_with_context: Observation
):
    """
    Test ability to complete suggestions.
    """
    assert suggestion_with_context.complete(score) == observation_with_context
