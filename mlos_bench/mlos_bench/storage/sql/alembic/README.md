# Schema Evolution with Alembic

This document contains some notes on how to use [`alembic`](https://alembic.sqlalchemy.org/en/latest/) for schema evolution in the `mlos_bench` project.

## Overview

1. Create a blank `mlos_bench.sqlite` database file in the [`mlos_bench/storage/sql`](../) directory with the current schema using the following command:

    ```sh
    cd mlos_bench/storage/sql
    rm mlos_bench.sqlite
    mlos_bench --storage storage/sqlite.jsonc --create-update-storage-schema-only
    ```

    > This allows `alembic` to automatically generate a migration script from the current schema.

2. Adjust the [`mlos_bench/storage/sql/schema.py`](../schema.py) file to reflect the new desired schema.

    > Keep each change small and atomic.
    > For example, if you want to add a new column, do that in one change.
    > If you want to rename a column, do that in another change.

3. Generate a new migration script with the following command:

    ```sh
    alembic revision --autogenerate -m "Descriptive text about the change."
    ```

4. Review the generated migration script in the [`mlos_bench/storage/sql/alembic/versions`](./versions/) directory.

5. Verify that the migration script works by running the following command:

    ```sh
    mlos_bench --storage storage/sqlite.jsonc --create-update-storage-schema-only
    ```

    > Normally this would be done with `alembic upgrade head`, but this command is convenient to ensure if will work with the `mlos_bench` command line interface as well.

6. If the migration script works, commit the changes to the [`mlos_bench/storage/sql/schema.py`](../schema.py) and [`mlos_bench/storage/sql/alembic/versions`](./versions/) files.

    > Be sure to update the latest version in the [`test_storage_schemas.py`](../../../tests/storage/test_storage_schemas.py) file as well.

7. Merge that to the `main` branch.

8. Might be good to cut a new `mlos_bench` release at this point as well.
