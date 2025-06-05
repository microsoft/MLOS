# Schema Evolution with Alembic

This document contains some notes on how to use [`alembic`](https://alembic.sqlalchemy.org/en/latest/) for schema evolution in the `mlos_bench` project.

## Overview

1. Create a blank database instance in the [`mlos_bench/storage/sql`](../) directory with the current schema using the following command:

   This allows `alembic` to automatically generate a migration script from the current schema.

   > NOTE: If your schema changes target a particular backend engine (e.g., using `with_variant`) you will need to use an engine with that config for this step.
   > \
   > In the remainder of this document we should some examples for different DB types.
   > Pick the one you're targeting and stick with it thru the example.
   > You may need to repeat the process several times to test all of them.
   >
   > - [ ] TODO: Add scripts to automatically do this for several different backend engines all at once.

   For instance:

   1. Start a temporary server either as a local file or in a docker instance

      ```sh
      # sqlite
      cd mlos_bench/storage/sql
      rm -f mlos_bench.sqlite
      ```

      ```sh
      # mysql
      docker run -it --rm --name mysql-alembic --env MYSQL_ROOT_PASSWORD=password --env MYSQL_DATABASE=mlos_bench -p 3306:3306 mysql:latest
      ```

      ```sh
      # postgres
      docker run -it --rm --name postgres-alembic --env POSTGRES_PASSWORD=password --env POSTGRES_DB=mlos_bench -p 5432:5432 postgres:latest
      ```

   1. Adjust the `sqlalchemy.url` in the [`alembic.ini`](../alembic.ini) file.

      ```ini
      # Uncomment one of these.
      # See README.md for details.

      #sqlalchemy.url = sqlite:///mlos_bench.sqlite
      sqlalchemy.url = mysql+pymysql://root:password@localhost:3306/mlos_bench
      #sqlalchemy.url = postgresql+psycopg2://root:password@localhost:5432/mlos_bench
      ```

   1. Prime the DB schema

      > Note: you may want to `git checkout main` first to make sure you're using the current schema here.

      ```sh
      # sqlite
      mlos_bench --storage storage/sqlite.jsonc --create-update-storage-schema-only --password=password
      ```

      ```sh
      # mysql
      mlos_bench --storage storage/mysql.jsonc --create-update-storage-schema-only --password=password
      ```

      ```sh
      # postgres
      mlos_bench --storage storage/postgresql.jsonc --create-update-storage-schema-only --password=password
      ```

1. Now, adjust the [`mlos_bench/storage/sql/schema.py`](../schema.py) file to reflect the new desired schema.

   > Don't forget to do this on a new branch.
   > \
   > Keep each change small and atomic.
   > \
   > For example, if you want to add a new column, do that in one change.
   > If you want to rename a column, do that in another change.

1. Generate a new migration script with the following command:

   ```sh
   alembic revision --autogenerate -m "CHANGEME: Descriptive text about the change."
   ```

1. Review the generated migration script in the [`mlos_bench/storage/sql/alembic/versions`](./versions/) directory.

1. Verify that the migration script works by running the following command:

   ```sh
   # sqlite
   mlos_bench --storage storage/sqlite.jsonc --create-update-storage-schema-only
   ```

   ```sh
   # mysql:
   mlos_bench --storage storage/mysql.jsonc --create-update-storage-schema-only --password=password
   ```

   ```sh
   # postgres:
   mlos_bench --storage storage/postgresql.jsonc --create-update-storage-schema-only --password=password
   ```

   > Normally this would be done with `alembic upgrade head`, but this command is convenient to ensure if will work with the `mlos_bench` command line interface as well.

   Examine the results using something like:

   ```sh
   # For sqlite:
   sqlite3 mlos_bench.sqlite .schema
   sqlite3 mlos_bench.sqlite "SELECT * FROM alembic_version;"
   ```

   ```sh
   # For mysql:
   mysql --user root --password=password --host localhost --protocol tcp --database mlos_bench -e "SHOW TABLES; SELECT * FROM alembic_version;"
   ```

   ```sh
   # For postgres:
   PGPASSWORD=password psql -h localhost -p 5432 -U postgres mlos_bench -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' and table_catalog='mlos_bench'; SELECT * FROM alembic_version;"
   ```

   > Use different CLI clients for targeting other engines.

1. If the migration script works, commit the changes to the [`mlos_bench/storage/sql/schema.py`](../schema.py) and [`mlos_bench/storage/sql/alembic/versions`](./versions/) files.

   > Be sure to update the latest version in the [`test_storage_schemas.py`](../../../tests/storage/test_storage_schemas.py) file as well.

1. Cleanup any server instances you started.

   For instance:

   ```sh
   rm mlos_bench/storage/sql/mlos_bench.sqlite
   ```

   ```sh
   docker kill mysql-alembic
   ```

   ```sh
   docker kill postgres-alembic
   ```

1. Merge that to the `main` branch.

1. Might be good to cut a new `mlos_bench` release at this point as well.
