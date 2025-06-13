# Sql Storage Tests

The "unit" tests for the `SqlStorage` classes are more functional than other unit tests in that we don't merely mock them out, but actually setup small SQL databases with `docker compose` and interact with them using the `SqlStorage` class.

To do this, we make use of the `pytest-docker` plugin to bring up the services defined in the [`docker-compose.yml`](./docker-compose.yml) file in this directory.

There are currently two services defined in that config, though others could be added in the future:

1. `mysql-mlos-bench-server`
1. `postgres-mlos-bench-server`

We rely on `docker compose` to map their internal container service ports to random ports on the host.
Hence, when connecting, we need to look up these ports on demand using something akin to `docker compose port`.
Because of complexities of networking in different development environments (especially for Docker on WSL2 for Windows), we may also have to connect to a different host address than `localhost` (e.g., `host.docker.internal`, which is dynamically requested as a part of of the [devcontainer](../../../../../../.devcontainer/docker-compose.yml) setup).

These containers are brought up as session fixtures under a unique (PID based) compose project name for each `pytest` invocation, but only when docker is detected on the host (via the `@docker_required` decorator we define in [`mlos_bench/tests/__init__.py`](../../../__init__.py)), else those tests are skipped.

> For manual testing, to bring up/down the test infrastructure the [`up.sh`](./up.sh) and [`down.sh`](./down.sh) scripts can be used, which assigns a known project name.

In the case of `pytest`, we also want to be able to test with a fresh state in most cases, so we use the `pytest` `yield` pattern to allow schema cleanup code to happen after the end of each test (see: `_create_storage_from_test_server_info`).
We use lockfiles to prevent races between tests that would otherwise try to create or cleanup the same database schema at the same time.

Additionally, since `scope="session"` fixtures are executed once per worker, which is excessive in our case, we use lockfiles (one of the only portable synchronization methods) to ensure that the usual `docker_services` fixture which starts and stops the containers is only executed once per test run and uses a shared compose instance.

## See Also

Notes in the [`mlos_bench/tests/services/remote/ssh/README.md`](../../../services/remote/ssh/README.md) file for a similar setup for SSH services.
