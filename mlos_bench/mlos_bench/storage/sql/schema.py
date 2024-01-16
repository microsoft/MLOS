#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
DB schema definition.
"""

import logging
from typing import List, Any

from sqlalchemy import (
    Engine, MetaData, Dialect, create_mock_engine,
    Table, Column, Sequence, Integer, Float, String, DateTime,
    PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint,
)

_LOG = logging.getLogger(__name__)

# This class is internal to SqlStorage and is mostly a struct
# for all DB tables, so it's ok to disable the warnings.
# pylint: disable=too-many-instance-attributes


class _DDL:
    """
    A helper class to capture the DDL statements from SQLAlchemy.

    It is used in `DbSchema.__str__()` method below.
    """

    def __init__(self, dialect: Dialect):
        self._dialect = dialect
        self.statements: List[str] = []

    def __call__(self, sql: Any, *_args: Any, **_kwargs: Any) -> None:
        self.statements.append(str(sql.compile(dialect=self._dialect)))

    def __repr__(self) -> str:
        res = ";\n".join(self.statements)
        return res + ";" if res else ""


class DbSchema:
    """
    A class to define and create the DB schema.
    """

    def __init__(self, engine: Engine):
        """
        Declare the SQLAlchemy schema for the database.
        """
        _LOG.info("Create the DB schema for: %s", engine)
        self._engine = engine
        self._meta = MetaData()

        self.experiment = Table(
            "experiment",
            self._meta,
            Column("exp_id", String(255), nullable=False),
            Column("description", String(1024)),
            Column("root_env_config", String(1024), nullable=False),
            Column("git_repo", String(1024), nullable=False),
            Column("git_commit", String(40), nullable=False),
            Column("optimization_target", String(1024), nullable=True),
            Column("optimization_direction", String(10), nullable=True),

            PrimaryKeyConstraint("exp_id"),
        )

        self.objectives = Table(
            "objectives",
            self._meta,
            Column("exp_id"),
            Column("optimization_target", String(1024), nullable=False),
            Column("optimization_direction", String(4), nullable=False),
            # TODO: Note: weight is not fully supported yet as currently
            # multi-objective is expected to explore each objective equally.
            # Will need to adjust the insert and return values to support this
            # eventually.
            Column("weight", Float, nullable=True),

            PrimaryKeyConstraint("exp_id", "optimization_target"),
            ForeignKeyConstraint(["exp_id"], [self.experiment.c.exp_id]),
        )

        # A workaround for SQLAlchemy issue with autoincrement in DuckDB:
        if engine.dialect.name == "duckdb":
            seq_config_id = Sequence('seq_config_id')
            col_config_id = Column("config_id", Integer, seq_config_id,
                                   server_default=seq_config_id.next_value(),
                                   nullable=False, primary_key=True)
        else:
            col_config_id = Column("config_id", Integer, nullable=False,
                                   primary_key=True, autoincrement=True)

        self.config = Table(
            "config",
            self._meta,
            col_config_id,
            Column("config_hash", String(64), nullable=False, unique=True),
        )

        self.trial = Table(
            "trial",
            self._meta,
            Column("exp_id", String(255), nullable=False),
            Column("trial_id", Integer, nullable=False),
            Column("config_id", Integer, nullable=False),
            Column("ts_start", DateTime, nullable=False, default="now"),
            Column("ts_end", DateTime),
            # Should match the text IDs of `mlos_bench.environments.Status` enum:
            Column("status", String(16), nullable=False),

            PrimaryKeyConstraint("exp_id", "trial_id"),
            ForeignKeyConstraint(["exp_id"], [self.experiment.c.exp_id]),
            ForeignKeyConstraint(["config_id"], [self.config.c.config_id]),
        )

        # Values of the tunable parameters of the experiment,
        # fixed for a particular trial config.
        self.config_param = Table(
            "config_param",
            self._meta,
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
            self._meta,
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
            self._meta,
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
            self._meta,
            Column("exp_id", String(255), nullable=False),
            Column("trial_id", Integer, nullable=False),
            Column("ts", DateTime, nullable=False, default="now"),
            Column("metric_id", String(255), nullable=False),
            Column("metric_value", String(255)),

            UniqueConstraint("exp_id", "trial_id", "ts", "metric_id"),
            ForeignKeyConstraint(["exp_id", "trial_id"],
                                 [self.trial.c.exp_id, self.trial.c.trial_id]),
        )

        _LOG.debug("Schema: %s", self._meta)

    def create(self) -> 'DbSchema':
        """
        Create the DB schema.
        """
        _LOG.info("Create the DB schema")
        self._meta.create_all(self._engine)
        return self

    def __repr__(self) -> str:
        """
        Produce a string with all SQL statements required to create the schema
        from scratch in current SQL dialect.

        That is, return a collection of CREATE TABLE statements and such.
        NOTE: this method is quite heavy! We use it only once at startup
        to log the schema, and if the logging level is set to DEBUG.

        Returns
        -------
        sql : str
            A multi-line string with SQL statements to create the DB schema from scratch.
        """
        ddl = _DDL(self._engine.dialect)
        mock_engine = create_mock_engine(self._engine.url, executor=ddl)
        self._meta.create_all(mock_engine, checkfirst=False)
        return str(ddl)
