#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for mlos_viz."""

import random
import warnings
from unittest.mock import Mock, patch

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_viz import MlosVizMethod, plot
from mlos_viz.tests import BASE_MATPLOTLIB_SHOW_PATCH, SEABORN_BOXPLOT_PATCH


def test_auto_method_type() -> None:
    """Ensure the AUTO method is what we expect."""
    assert MlosVizMethod.AUTO.value == MlosVizMethod.DABL.value


@patch(BASE_MATPLOTLIB_SHOW_PATCH)
@patch(SEABORN_BOXPLOT_PATCH)
def test_plot(mock_show: Mock, mock_boxplot: Mock, exp_data: ExperimentData) -> None:
    """Tests core plot() API."""
    # For now, just ensure that no errors are thrown.
    # TODO: Check that a plot was actually produced matching our specifications.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        random.seed(42)
        plot(exp_data, filter_warnings=True)
    assert mock_show.call_count >= 2  # from the two base plots and anything dabl did
    assert mock_boxplot.call_count >= 1  # from anything dabl did
