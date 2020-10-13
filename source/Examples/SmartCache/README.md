# [SmartCache Example](./#mlos-github-tree-view)

This [`SmartCache`](./#mlos-github-tree-view) example is a C++ implementation of the [Python SmartCache](../../Mlos.Python/mlos/Examples/SmartCache/#mlos-github-tree-view).

It implements a simple cache with different replacement policies and cache size as built-in tunables and some simple workloads.

It can be used to demonstrate a full end-to-end MLOS integrated microbenchmark for a "smart" component (in this case a cache).

## Overview

To do that, we run the (C++) `SmartCache` executable to communicate with the (C#) [`Mlos.Agent.Server`](../../Mlos.Agent.Server/#mlos-github-tree-view) over a shared memory channel provided by the [`Mlos.Core`](../../Mlos.Core/#mlos-github-tree-view) library.

The `Mlos.Agent.Server` is essentially a small wrapper around several other communication channels to allow different components to connect for component experimentation convenience.

It provides

1. Shared memory communication channels via the [`Mlos.Agent`](../../Mlos.Agent/#mlos-github-tree-view) and [`Mlos.NetCore`](../../Mlos.NetCore/#mlos-github-tree-view) libraries.

2. A [`Mlos.Agent.GrpcServer`](../../Mlos.Agent.GrpcClient/#mlos-github-tree-view) GRPC channel to allow driving the experimentation process from a Jupyter notebook.

3. A GRPC client to connect to the (Python) [`mlos.Grpc.OptimizerMicroserviceServer`](../../Mlos.Python/mlos/Grpc/OptimizerMicroserviceServer.py#mlos-github-tree-view) to store and track those experiments.

TODO: Diagrams

## Building

> Note: these commands are given relative to the root of the MLOS repo.
>
> To move there, you can execute the following within the repository:
>
> `cd $(git rev-parse --show-toplevel)`

To build and run the necessary components for this example

1. [Pull or build the Docker image](../../../documentation/01-Prerequisites.md#build-the-docker-image) using the [`Dockerfile`](../../../Dockerfile#mlos-github-tree-view) at the root of the repository.

    ```shell
    docker build . --build-arg=UbuntuVersion=20.04 -t mlos-build-ubuntu-20.04 \
        --cache-from ghcr.io/microsoft-cisl/mlos/mlos-build-ubuntu-20.04
    ```

2. [Run the Docker image](../../../documentation/02-Build.md#create-a-new-container-instance) you just built.

    ```shell
    docker run -it -v $PWD:/src/MLOS -P --name mlos-build mlos-build-ubuntu-20.04
    ```

3. Inside the container, [build the compiled software](../../../documentation/02-Build.md#cli-make) with `make`:

    ```sh
    make all install
    ```

    > This will build everything using a default `CONFIGURATION=Release`.
    >
    > To just build `SmartCache` and `Mlos.Agent.Server`, execute the following:

      ```sh
      # Alternatively:
      make -C source/Mlos.Agent.Server
      make -C source/Examples/SmartCache all install
      ```

4. For a `Release` build (the default), the relevant output will be installed at:

    - Mlos.Agent.Server:

        `target/bin/Release/AnyCPU/Mlos.Agent.Server/Mlos.Agent.Server.dll`

    - SmartCache:

        `target/bin/Release/x86_64/SmartCache`

    - SmartCache.SettingsRegistry:

        `target/bin/Release/AnyCPU/SmartCache.SettingsRegistry.dll`

## Executing

The following commands will start the `Mlos.Server.Agent` and cause it to start the `SmartCache` component microbenchmark:

```sh
tools/bin/dotnet target/bin/Release/AnyCPU/Mlos.Agent.Server/Mlos.Agent.Server.dll \
    --executable target/bin/Release/x86_64/SmartCache \
    --settings-registry-path target/bin/Release/AnyCPU
    --optimizer-uri http://localhost:50051
```

```txt
Mlos.Agent.Server
Starting target/bin/Release/x86_64/SmartCache
observations: 0
warn: Microsoft.AspNetCore.Server.Kestrel[0]
      Unable to bind to http://localhost:5000 on the IPv6 loopback interface: 'Cannot assign requested address'.
info: Microsoft.Hosting.Lifetime[0]
      Now listening on: http://localhost:5000
info: Microsoft.Hosting.Lifetime[0]
      Application started. Press Ctrl+C to shut down.
info: Microsoft.Hosting.Lifetime[0]
      Hosting environment: Production
info: Microsoft.Hosting.Lifetime[0]
      Content root path: /src/MLOS
Starting Mlos.Agent
Found settings registry assembly at target/bin/Release/AnyCPU/SmartCache.SettingsRegistry.dll
observations: 1
observations: 2
observations: 3
...
```

### Explanation

The `Mlos.Agent` that gets started by the `Mlos.Agent.Server` waits for a signal that the component (`SmartCache`) has connected to the shared memory region before starting to poll the component for messages to process.
This is important in case the component is started independently.

In this case, `Mlos.Agent.Server` itself starts the component.

Once started, `SmartCache` will attempt to register its component specific set of shared memory messages with the `Mlos.Agent` in the `Mlos.Agent.Server` using `RegisterComponentConfig` and `RegisterAssemblyRequestMessage` from `Mlos.Core` and `Mlos.NetCore`.
That includes the name of the `SettingsRegistry` assembly (`.dll`) corresponding to that component's settings/messages.

The `Mlos.Agent.Server` needs to be told where it can find those assemblies in order to load them so that it can process the messages sent by the component.
To do that, we use the `--settings-registry-path` option.

We also tell the `Mlos.Agent.Server` how to connect to the (Python) MLOS Optimizer Service over GRPC so that the application message handlers setup by the `SmartCache.SettingsRegistry` for the agent can request new configuration recommendations on behave of the application.

For additional details please see the comments in the following code files:

- [Mlos.Agent.Server/MlosAgentServer.cs](../../Mlos.Agent.Server/MlosAgentServer.cs#mlos-github-tree-view)
- [SmartCache/Main.cpp](./Main.cpp#mlos-github-tree-view)
- [SmartCache.SettingsRegistry/AssemblyInitializer.cs](./SmartCache.SettingsRegistry/AssemblyInitializer.cs#mlos-github-tree-view)
- [SmartCache.SettingsRegistry/Codegen/SmartCache.cs](./SmartCache.SettingsRegistry/Codegen/SmartCache.cs#mlos-github-tree-view)

## Caveats

- The system currently only supports one shared memory region and doesn't cleanup the shared memory after itself.

    As such, you may see hung processes when restarting after a failed experiment.

    To help with this, we currently provide a helper script to remove previous incarnations of the shared memory regions:

    ```sh
    build/CMakeHelpers/RemoveMlosSharedMemories.sh
    ```

    You may also need to make sure that the processes using them are killed off.
    For instance:

    ```sh
    pkill SmartCache
    pkill -f dotnet.*Mlos.Agent.Server.dll
    ```

    > Note: each of these commands should be executed inside the `Mlos.Agent.Server` execution environment (e.g. inside the docker container).
