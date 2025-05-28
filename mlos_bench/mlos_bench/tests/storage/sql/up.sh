#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# A script to start the containerized SQL DBMS servers.
# For pytest, the fixture in conftest.py will handle this for us using the
# pytest-docker plugin, but for manual testing, this script can be used.

set -eu
set -x

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

PROJECT_NAME="mlos_bench-test-sql-storage-manual"
CONTAINER_COUNT=2

if ! type mysqladmin >/dev/null 2>&1; then
    echo "ERROR: Missing mysqladmin tool to check status of the server." >&2
    exit 1
fi

if ! type psql >/dev/null 2>&1; then
    echo "ERROR: Missing psql tool to check status of the server." >&2
    exit 1
fi


docker compose -p "$PROJECT_NAME" up --build --remove-orphans -d
set +x

while ! docker compose -p "$PROJECT_NAME" ps --format '{{.Name}} {{.State}} {{.Health}}' | grep -c ' running healthy$' | grep -q -x $CONTAINER_COUNT; do
    echo "Waiting for $CONTAINER_COUNT containers to report healthy ..."
    sleep 1
done

mysql_port=$(docker compose -p "$PROJECT_NAME" port mysql-mlos-bench-server ${PORT:-3306} | cut -d: -f2)
echo "Connect to the mysql server container at the following port: $mysql_port"
postgres_port=$(docker compose -p "$PROJECT_NAME" port postgres-mlos-bench-server ${PORT:-5432} | cut -d: -f2)
echo "Connect to the postgres server container at the following port: $postgres_port"

# TODO: Remove the rest of this:

mysql_ok=0
if ! type mysqladmin >/dev/null 2>&1; then
    echo "WARNING: Missing mysqladmin tool to check status of the server." >&2
    mysql_ok=1
fi

pg_ok=0
if ! type psql >/dev/null 2>&1; then
    echo "WARNING: Missing psql tool to check status of the server." >&2
    pg_ok=1
fi

for i in {1..10}; do
    if [ "$mysql_ok" == "1" ]; then
        break
    fi
    if mysqladmin -h localhost --port $mysql_port --protocol tcp --password=password ping >/dev/null; then
        mysql_ok=1
    else
        sleep 1
    fi
done
if [ "$mysql_ok" != 1 ]; then
    echo "ERR: MySQL failed to start." >&2
    exit 1
fi

for i in {1..10}; do
    if [ "$pg_ok" == "1" ]; then
        break
    fi
    if PGPASSWORD=password psql -h localhost -p $postgres_port -U postgres mlos_bench -c "SELECT 1;" > /dev/null; then
        pg_ok=1
        break
    else
        sleep 1
    fi
done
if [ "$pg_ok" != 1 ]; then
    echo "ERR: Postgres failed to start." >&2
    exit 1
fi
