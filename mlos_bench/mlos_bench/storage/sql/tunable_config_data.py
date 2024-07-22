#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""An interface to access the tunable config data stored in SQL DB."""

import pandas
from sqlalchemy import Engine

from mlos_bench.storage.base_tunable_config_data import TunableConfigData
from mlos_bench.storage.sql.schema import DbSchema


class TunableConfigSqlData(TunableConfigData):
    """
    SQL interface for accessing the stored experiment benchmark (tunable) config data.

    A configuration in this context is the set of tunable parameter values.
    """

    def __init__(self, *, engine: Engine, schema: DbSchema, tunable_config_id: int):
        super().__init__(tunable_config_id=tunable_config_id)
        self._engine = engine
        self._schema = schema

    @property
    def config_df(self) -> pandas.DataFrame:
        with self._engine.connect() as conn:
            cur_config = conn.execute(
                self._schema.config_param.select()
                .where(self._schema.config_param.c.config_id == self._tunable_config_id)
                .order_by(
                    self._schema.config_param.c.param_id,
                )
            )
            return pandas.DataFrame(
                [(row.param_id, row.param_value) for row in cur_config.fetchall()],
                columns=["parameter", "value"],
            )
