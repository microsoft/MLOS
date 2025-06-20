#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common SQL methods for accessing the stored benchmark data."""

from collections.abc import Mapping
from typing import Any

import pandas
from sqlalchemy import Integer, and_, func, select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.schema import Table

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.util import nullable, utcify_nullable_timestamp, utcify_timestamp


def save_params(
    conn: Connection,
    table: Table,
    params: Mapping[str, Any],
    **kwargs: Any,
) -> None:
    """
    Updates a set of (param_id, param_value) tuples in the given Table.

    Parameters
    ----------
    conn : sqlalchemy.engine.Connection
        A connection to the backend database.
    table : sqlalchemy.schema.Table
        The table to update.
    params : dict[str, Any]
        The new (param_id, param_value) tuples to upsert to the Table.
    **kwargs : dict[str, Any]
        Primary key info for the given table.
    """
    if not params:
        return
    conn.execute(
        table.insert(),
        [
            {**kwargs, "param_id": key, "param_value": nullable(str, val)}
            for (key, val) in params.items()
        ],
    )


def get_trials(
    engine: Engine,
    schema: DbSchema,
    experiment_id: str,
    tunable_config_id: int | None = None,
) -> dict[int, TrialData]:
    """
    Gets :py:class:`~.TrialData` for the given ``experiment_id`` and optionally
    additionally restricted by ``tunable_config_id``.

    See Also
    --------
    :py:class:`~mlos_bench.storage.sql.tunable_config_trial_group_data.TunableConfigTrialGroupSqlData`
    :py:class:`~mlos_bench.storage.sql.experiment_data.ExperimentSqlData`
    """  # pylint: disable=line-too-long # noqa: E501
    # pylint: disable=import-outside-toplevel,cyclic-import
    from mlos_bench.storage.sql.trial_data import TrialSqlData

    with engine.connect() as conn:
        # Build up sql a statement for fetching trials.
        stmt = (
            schema.trial.select()
            .where(
                schema.trial.c.exp_id == experiment_id,
            )
            .order_by(
                schema.trial.c.exp_id.asc(),
                schema.trial.c.trial_id.asc(),
            )
        )
        # Optionally restrict to those using a particular tunable config.
        if tunable_config_id is not None:
            stmt = stmt.where(
                schema.trial.c.config_id == tunable_config_id,
            )
        trials = conn.execute(stmt)
        return {
            trial.trial_id: TrialSqlData(
                engine=engine,
                schema=schema,
                experiment_id=experiment_id,
                trial_id=trial.trial_id,
                config_id=trial.config_id,
                ts_start=utcify_timestamp(trial.ts_start, origin="utc"),
                ts_end=utcify_nullable_timestamp(trial.ts_end, origin="utc"),
                status=Status.parse(trial.status),
                trial_runner_id=trial.trial_runner_id,
            )
            for trial in trials.fetchall()
        }


def get_results_df(
    engine: Engine,
    schema: DbSchema,
    experiment_id: str,
    tunable_config_id: int | None = None,
) -> pandas.DataFrame:
    """
    Gets TrialData for the given experiment_id and optionally additionally restricted by
    tunable_config_id.

    The returned DataFrame includes each trial's metadata, config, and results in
    wide format, with config parameters prefixed with
    :py:attr:`.ExperimentData.CONFIG_COLUMN_PREFIX` and results prefixed with
    :py:attr:`.ExperimentData.RESULT_COLUMN_PREFIX`.

    See Also
    --------
    :py:class:`~mlos_bench.storage.sql.tunable_config_trial_group_data.TunableConfigTrialGroupSqlData`
    :py:class:`~mlos_bench.storage.sql.experiment_data.ExperimentSqlData`
    """  # pylint: disable=line-too-long # noqa: E501
    # pylint: disable=too-many-locals
    with engine.connect() as conn:
        # Compose a subquery to fetch the tunable_config_trial_group_id for each tunable config.
        tunable_config_group_id_stmt = (
            schema.trial.select()
            .with_only_columns(
                schema.trial.c.exp_id,
                schema.trial.c.config_id,
                func.min(schema.trial.c.trial_id)
                .cast(Integer)
                .label("tunable_config_trial_group_id"),
            )
            .where(
                schema.trial.c.exp_id == experiment_id,
            )
            .group_by(
                schema.trial.c.exp_id,
                schema.trial.c.config_id,
            )
        )
        # Optionally restrict to those using a particular tunable config.
        if tunable_config_id is not None:
            tunable_config_group_id_stmt = tunable_config_group_id_stmt.where(
                schema.trial.c.config_id == tunable_config_id,
            )
        tunable_config_trial_group_id_subquery = tunable_config_group_id_stmt.subquery()

        # Get each trial's metadata.
        cur_trials_stmt = (
            select(
                schema.trial,
                tunable_config_trial_group_id_subquery,
            )
            .where(
                schema.trial.c.exp_id == experiment_id,
                and_(
                    tunable_config_trial_group_id_subquery.c.exp_id == schema.trial.c.exp_id,
                    tunable_config_trial_group_id_subquery.c.config_id == schema.trial.c.config_id,
                ),
            )
            .order_by(
                schema.trial.c.exp_id.asc(),
                schema.trial.c.trial_id.asc(),
            )
        )
        # Optionally restrict to those using a particular tunable config.
        if tunable_config_id is not None:
            cur_trials_stmt = cur_trials_stmt.where(
                schema.trial.c.config_id == tunable_config_id,
            )
        cur_trials = conn.execute(cur_trials_stmt)
        trials_df = pandas.DataFrame(
            [
                (
                    row.trial_id,
                    utcify_timestamp(row.ts_start, origin="utc"),
                    utcify_nullable_timestamp(row.ts_end, origin="utc"),
                    row.config_id,
                    row.tunable_config_trial_group_id,
                    row.status,
                    row.trial_runner_id,
                )
                for row in cur_trials.fetchall()
            ],
            columns=[
                "trial_id",
                "ts_start",
                "ts_end",
                "tunable_config_id",
                "tunable_config_trial_group_id",
                "status",
                "trial_runner_id",
            ],
        )

        # Get each trial's config in wide format.
        configs_stmt = (
            schema.trial.select()
            .with_only_columns(
                schema.trial.c.trial_id,
                schema.trial.c.config_id,
                schema.config_param.c.param_id,
                schema.config_param.c.param_value,
            )
            .where(
                schema.trial.c.exp_id == experiment_id,
            )
            .join(
                schema.config_param,
                schema.config_param.c.config_id == schema.trial.c.config_id,
            )
            .order_by(
                schema.trial.c.trial_id,
                schema.config_param.c.param_id,
            )
        )
        if tunable_config_id is not None:
            configs_stmt = configs_stmt.where(
                schema.trial.c.config_id == tunable_config_id,
            )
        configs = conn.execute(configs_stmt)
        configs_df = pandas.DataFrame(
            [
                (
                    row.trial_id,
                    row.config_id,
                    ExperimentData.CONFIG_COLUMN_PREFIX + row.param_id,
                    row.param_value,
                )
                for row in configs.fetchall()
            ],
            columns=["trial_id", "tunable_config_id", "param", "value"],
        ).pivot(
            index=["trial_id", "tunable_config_id"],
            columns="param",
            values="value",
        )
        configs_df = configs_df.apply(
            pandas.to_numeric,
            errors="coerce",
        ).fillna(configs_df)

        # Get each trial's results in wide format.
        results_stmt = (
            schema.trial_result.select()
            .with_only_columns(
                schema.trial_result.c.trial_id,
                schema.trial_result.c.metric_id,
                schema.trial_result.c.metric_value,
            )
            .where(
                schema.trial_result.c.exp_id == experiment_id,
            )
            .order_by(
                schema.trial_result.c.trial_id,
                schema.trial_result.c.metric_id,
            )
        )
        if tunable_config_id is not None:
            results_stmt = results_stmt.join(
                schema.trial,
                and_(
                    schema.trial.c.exp_id == schema.trial_result.c.exp_id,
                    schema.trial.c.trial_id == schema.trial_result.c.trial_id,
                    schema.trial.c.config_id == tunable_config_id,
                ),
            )
        results = conn.execute(results_stmt)
        results_df = pandas.DataFrame(
            [
                (
                    row.trial_id,
                    ExperimentData.RESULT_COLUMN_PREFIX + row.metric_id,
                    row.metric_value,
                )
                for row in results.fetchall()
            ],
            columns=["trial_id", "metric", "value"],
        ).pivot(
            index="trial_id",
            columns="metric",
            values="value",
        )
        results_df = results_df.apply(
            pandas.to_numeric,
            errors="coerce",
        ).fillna(results_df)

        # Concat the trials, configs, and results.
        return trials_df.merge(configs_df, on=["trial_id", "tunable_config_id"], how="left").merge(
            results_df,
            on="trial_id",
            how="left",
        )
