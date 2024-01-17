#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mlos_viz.
"""

import warnings

from mlos_bench.storage.base_experiment_data import ExperimentData

from mlos_viz import MlosVizMethod, ignore_plotter_warnings, plot


def test_auto_method_type() -> None:
    """Ensure the AUTO method is what we expect."""
    assert MlosVizMethod.AUTO.value == MlosVizMethod.DABL.value


def test_plot(exp_data: ExperimentData) -> None:
    """Tests plotting via dabl."""
    # For now, just ensure that no errors are thrown.
    # TODO: Check that a plot was actually produced matching our specifications.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ignore_plotter_warnings()
        plot(exp_data)
