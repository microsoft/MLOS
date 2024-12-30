#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Interfaces to the SQL-based storage backends for mlos_bench using `SQLAlchemy
<https://www.sqlalchemy.org/>`_.

In general any SQL system supported by SQLAlchemy can be used, but the default is a
local SQLite instance.

Although the schema is defined (and printable) by the
:py:mod:`mlos_bench.storage.sql.schema` module so direct queries are possible, users
are expected to interact with the data using the
:py:class:`~mlos_bench.storage.sql.experiment_data.ExperimentSqlData` and
:py:class:`~mlos_bench.storage.sql.trial_data.TrialSqlData` interfaces, which can be
obtained from the initial :py:class:`.SqlStorage` instance obtained by
:py:func:`mlos_bench.storage.storage_factory.from_config`.

Notes
-----
See the `mlos_bench/config/storage
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/storage>`_
tree for some configuration examples.

See Also
--------
:py:mod:`mlos_bench.storage` : The base storage module for mlos_bench, which
    includes some basic examples in the documentation.
"""
from mlos_bench.storage.sql.storage import SqlStorage

__all__ = [
    "SqlStorage",
]
