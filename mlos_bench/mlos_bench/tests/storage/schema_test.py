#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Regression tests for SQL schema migration configuration."""

from pathlib import Path

import pytest
from sqlalchemy import URL, create_engine

from mlos_bench.storage.sql.schema import DbSchema


@pytest.mark.parametrize("database", [":memory:", "database%name.sqlite", "database name.sqlite"])
def test_alembic_url_round_trip(database: str, tmp_path: Path) -> None:
    """Preserve URL escaping when Alembic reads its interpolated configuration."""
    if database != ":memory:":
        database = str(tmp_path / database)
    engine = create_engine(URL.create("sqlite", database=database))
    try:
        schema = DbSchema(engine)
        with engine.connect() as connection:
            config = schema._get_alembic_cfg(connection)  # pylint: disable=protected-access
            assert config.get_main_option("sqlalchemy.url") == engine.url.render_as_string(
                hide_password=False,
            )
            assert config.attributes["connection"] is connection
    finally:
        engine.dispose()
