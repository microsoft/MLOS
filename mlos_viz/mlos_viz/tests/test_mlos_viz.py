#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mlos_viz.
"""

import warnings

from unittest.mock import patch, Mock

from mlos_bench.storage.base_experiment_data import ExperimentData

from mlos_viz import MlosVizMethod, plot


def test_auto_method_type() -> None:
    """Ensure the AUTO method is what we expect."""
    assert MlosVizMethod.AUTO.value == MlosVizMethod.DABL.value


@patch("mlos_viz.base.plt.show")
def test_plot(mock_show: Mock, exp_data: ExperimentData) -> None:
    """Tests core plot() API."""
    # For now, just ensure that no errors are thrown.
    # TODO: Check that a plot was actually produced matching our specifications.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        plot(exp_data, filter_warnings=True)
    assert mock_show.call_count == 1
