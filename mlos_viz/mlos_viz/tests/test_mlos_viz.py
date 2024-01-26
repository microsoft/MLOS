#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mlos_viz.
"""

import random
import warnings

from unittest.mock import patch, Mock

from mlos_bench.storage.base_experiment_data import ExperimentData

from mlos_viz import MlosVizMethod, plot


def test_auto_method_type() -> None:
    """Ensure the AUTO method is what we expect."""
    assert MlosVizMethod.AUTO.value == MlosVizMethod.DABL.value


@patch("mlos_viz.base.plt.show")
@patch("dabl.plot.supervised.sns.boxplot")
def test_plot(mock_show: Mock, mock_boxplot: Mock, exp_data: ExperimentData) -> None:
    """Tests core plot() API."""
    # For now, just ensure that no errors are thrown.
    # TODO: Check that a plot was actually produced matching our specifications.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        random.seed(42)
        plot(exp_data, filter_warnings=True)
    assert mock_show.call_count >= 2        # from the two base plots and anything dabl did
    assert mock_boxplot.call_count >= 1     # from anything dabl did
