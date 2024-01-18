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

from mlos_viz.base import ignore_plotter_warnings, plot_optimizer_trends, plot_top_n_configs


@patch("mlos_viz.base.plt.show")
def test_plot_optimizer_trends(mock_show: Mock, exp_data: ExperimentData) -> None:
    """Tests plotting optimizer trends."""
    # For now, just ensure that no errors are thrown.
    # TODO: Check that a plot was actually produced matching our specifications.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ignore_plotter_warnings()
        plot_optimizer_trends(exp_data)
    assert mock_show.call_count == 1


@patch("mlos_viz.base.plt.show")
def test_plot_top_n_configs(mock_show: Mock, exp_data: ExperimentData) -> None:
    """Tests plotting top N configs."""
    # For now, just ensure that no errors are thrown.
    # TODO: Check that a plot was actually produced matching our specifications.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ignore_plotter_warnings()
        plot_top_n_configs(exp_data)
    assert mock_show.call_count == 1
