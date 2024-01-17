#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mlos_viz.
"""

from mlos_viz import MlosVizMethod


def test_auto_method_type() -> None:
    """Ensure the AUTO method is what we expect."""
    assert MlosVizMethod.AUTO.value == MlosVizMethod.DABL.value


def test_plot() -> None:
    raise NotImplementedError("TODO")
