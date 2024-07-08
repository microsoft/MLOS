#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for mlos_viz."""

import sys

import seaborn  # pylint: disable=unused-import     # (used by patch)   # noqa: unused

BASE_MATPLOTLIB_SHOW_PATCH = "mlos_viz.base.plt.show"

if sys.version_info >= (3, 11):
    SEABORN_BOXPLOT_PATCH = "dabl.plot.supervised.sns.boxplot"
else:
    SEABORN_BOXPLOT_PATCH = "seaborn.boxplot"
