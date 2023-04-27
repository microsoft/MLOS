# Services

Services are essentially a collection of helper functions used to `setup`, `run`, and `teardown` an [`Environment`](../environments/) in the [`mlos_bench`](../../../mlos_bench/) benchmarking automation framework.

They are (roughly) divided into two categories:

- `LocalService` - A service that runs on the same machine as the scheduler component.

    This may be things like executing a script for parsing the results of a benchmark run using local tools that aren't necessarily available on the target system.

- `RemoteService` - A service that runs on a remote (target) machine.

    This may be things like executing a script on a remote machine to start a benchmark run.
