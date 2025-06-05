# SshServices Testing

The "unit" tests for the `SshService` classes are more functional than other unit tests in that we don't merely mock them out, but actually setup small SSH servers with `docker compose` and interact with them using the `SshHostService` and `SshFileShareService`.

To do this, we make use of the `pytest-docker` plugin to bring up the services defined in the [`docker-compose.yml`](./docker-compose.yml) file in this directory.

There are two services defined in that config:

1. `ssh-server`
1. `alt-server`

We rely on `docker compose` to map their internal container service ports to random ports on the host.
Hence, when connecting, we need to look up these ports on demand using something akin to `docker compose port`.
Because of complexities of networking in different development environments (especially for Docker on WSL2 for Windows), we may also have to connect to a different host address than `localhost` (e.g., `host.docker.internal`, which is dynamically requested as a part of of the [devcontainer](../../../../../../.devcontainer/docker-compose.yml) setup).

Both containers run the same image, which is dynamically built, and defined in the [`Dockerfile`](./Dockerfile).
This will dynamically generate a passphrase-less ssh key (`id_rsa`) stored inside the image that can be `docker cp`-ed out and then used to authenticate `ssh` clients into that instance.

These are brought up as session fixtures under a unique (PID based) compose project name for each `pytest` invocation, but only when docker is detected on the host (via the `@docker_required` decorator we define in [`mlos_bench/tests/__init__.py`](../../../__init__.py)), else those tests are skipped.

> For manual testing, to bring up/down the test infrastructure the [`up.sh`](./up.sh) and [`down.sh`](./down.sh) scripts can be used, which assigns a known project name.

In the case of `pytest`, since the `SshService` base class implements a shared connection cache that we wish to test, and testing "rebooting" of servers (containers) is also necessary, but we want to avoid single threaded execution for tests, we start a third container only for testing reboots.

Additionally, since `scope="session"` fixtures are executed once per worker, which is excessive in our case, we use lockfiles (one of the only portable synchronization methods) to ensure that the usual `docker_services` fixture which starts and stops the containers is only executed once per test run and uses a shared compose instance.

## See Also

Notes in the [`SshService`](../../../../services/remote/ssh/ssh_service.py) implementation.
