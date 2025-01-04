#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Utility functions for manipulating experiment results data."""
from typing import Literal

import pandas

from mlos_bench.storage.base_experiment_data import ExperimentData


def expand_results_data_args(
    exp_data: ExperimentData | None = None,
    results_df: pandas.DataFrame | None = None,
    objectives: dict[str, Literal["min", "max"]] | None = None,
) -> tuple[pandas.DataFrame, dict[str, bool]]:
    """
    Expands some common arguments for working with results data.

    Used by mlos_viz as well.

    Parameters
    ----------
    exp_data : ExperimentData | None
        ExperimentData to operate on.
    results_df : pandas.DataFrame | None
        Optional results_df argument.
        If not provided, defaults to :py:attr:`.ExperimentData.results_df` property.
    objectives : Optional[dict[str, Literal["min", "max"]]]
        Optional objectives set to operate on.
        If not provided, defaults to :py:attr:`.ExperimentData.objectives` property.

    Returns
    -------
    tuple[pandas.DataFrame, dict[str, bool]]
        The results dataframe and the objectives columns in the dataframe, plus
        whether or not they are in ascending order.
    """
    # Prepare the orderby columns.
    if results_df is None:
        if exp_data is None:
            raise ValueError("Must provide either exp_data or both results_df and objectives.")
        results_df = exp_data.results_df

    if objectives is None:
        if exp_data is None:
            raise ValueError("Must provide either exp_data or both results_df and objectives.")
        objectives = exp_data.objectives
    objs_cols: dict[str, bool] = {}
    for opt_tgt, opt_dir in objectives.items():
        if opt_dir not in ["min", "max"]:
            raise ValueError(f"Unexpected optimization direction for target {opt_tgt}: {opt_dir}")
        ascending = opt_dir == "min"
        if (
            opt_tgt.startswith(ExperimentData.RESULT_COLUMN_PREFIX)
            and opt_tgt in results_df.columns
        ):
            objs_cols[opt_tgt] = ascending
        elif ExperimentData.RESULT_COLUMN_PREFIX + opt_tgt in results_df.columns:
            objs_cols[ExperimentData.RESULT_COLUMN_PREFIX + opt_tgt] = ascending
        else:
            raise UserWarning(f"{opt_tgt} is not a result column for experiment {exp_data}")
    # Note: these copies are important to avoid issues with downstream consumers.
    # It is more efficient to copy the dataframe than to go back to the original data source.
    # TODO: However, it should be possible to later fixup the downstream consumers
    # (which are currently still internal to mlos-viz) to make their own data
    # sources if necessary.  That will of course need tests.
    return (results_df.copy(), objs_cols.copy())
