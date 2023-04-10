#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
DB schema definition.
"""

import logging

from sqlalchemy import (
    MetaData, Table, Column, Integer, String, DateTime,
    PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint,
)

_LOG = logging.getLogger(__name__)


class DbSchema:
    """
    A class to define and create the DB schema.
    """

    def __init__(self):
        """
        Declare the SQLAlchemy schema for the database.
        """
        _LOG.info("Create the DB schema")
        self.meta = MetaData()

        self.experiment = Table(
            "experiment",
            self.meta,
            Column("exp_id", String(255), nullable=False),
            Column("description", String),
            Column("metric_id", String(255), nullable=False),  # Optimization target
            Column("git_repo", String, nullable=False),
            Column("git_commit", String(40), nullable=False),

            PrimaryKeyConstraint("exp_id"),
        )

        self.config = Table(
            "config",
            self.meta,
            Column("config_id", Integer, nullable=False, autoincrement=True),
            Column("config_hash", String, nullable=False, unique=True),

            PrimaryKeyConstraint("config_id"),
        )

        self.trial = Table(
            "trial",
            self.meta,
            Column("exp_id", String(255), nullable=False),
            Column("trial_id", Integer, nullable=False),
            Column("config_id", Integer, nullable=False),
            Column("ts_start", DateTime, nullable=False, default="now"),
            Column("ts_end", DateTime),
            # Should match the text IDs of `mlos_bench.environment.Status` enum:
            Column("status", String(16), nullable=False),

            PrimaryKeyConstraint("exp_id", "trial_id"),
            ForeignKeyConstraint(["exp_id"], [self.experiment.c.exp_id]),
            ForeignKeyConstraint(["config_id"], [self.config.c.config_id]),
        )

        # Values of the tunable parameters of the experiment,
        # fixed for a particular trial config.
        self.config_param = Table(
            "config_param",
            self.meta,
            Column("config_id", Integer, nullable=False),
            Column("param_id", String(255), nullable=False),
            Column("param_value", String(255)),

            PrimaryKeyConstraint("config_id", "param_id"),
            ForeignKeyConstraint(["config_id"], [self.config.c.config_id]),
        )

        # Values of additional non-tunable parameters of the trial,
        # e.g., scheduled execution time, VM name / location, number of repeats, etc.
        self.trial_param = Table(
            "trial_param",
            self.meta,
            Column("exp_id", String(255), nullable=False),
            Column("trial_id", Integer, nullable=False),
            Column("param_id", String(255), nullable=False),
            Column("param_value", String(255)),

            PrimaryKeyConstraint("exp_id", "trial_id", "param_id"),
            ForeignKeyConstraint(["exp_id", "trial_id"],
                                 [self.trial.c.exp_id, self.trial.c.trial_id]),
        )

        self.trial_result = Table(
            "trial_result",
            self.meta,
            Column("exp_id", String(255), nullable=False),
            Column("trial_id", Integer, nullable=False),
            Column("metric_id", String(255), nullable=False),
            Column("metric_value", String(255)),

            PrimaryKeyConstraint("exp_id", "trial_id", "metric_id"),
            ForeignKeyConstraint(["exp_id", "trial_id"],
                                 [self.trial.c.exp_id, self.trial.c.trial_id]),
        )

        self.trial_telemetry = Table(
            "trial_telemetry",
            self.meta,
            Column("exp_id", String(255), nullable=False),
            Column("trial_id", Integer, nullable=False),
            Column("ts", DateTime, nullable=False, default="now"),
            Column("metric_id", String(255), nullable=False),
            Column("metric_value", String(255)),

            UniqueConstraint("exp_id", "trial_id", "ts", "metric_id"),
            ForeignKeyConstraint(["exp_id", "trial_id"],
                                 [self.trial.c.exp_id, self.trial.c.trial_id]),
        )

        _LOG.debug("Schema: %s", self.meta)

    def create(self, engine):
        """
        Create the DB schema.
        """
        _LOG.info("Create the DB schema")
        self.meta.create_all(engine)
        return self
