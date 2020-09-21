# SmartCache Example

TODO: Some description of the example contained in this directory.

This `SmartCache` can be used to demonstrate a full end-to-end MLOS integrated microbenchmark for a "smart" component (in this case a cache).

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

1. [Build the Docker image](../../../documentation/01-Prerequisites.md#build-the-docker-image) using the [`Dockerfile`](../../../Dockerfile#mlos-github-tree-view) at the root of the repository.

    ```shell
    docker build --build-arg=UbuntuVersion=20.04 -t mlos/build:ubuntu-20.04 .
    ```

2. [Run the Docker image](../../../documentation/02-Build.md#create-a-new-container-instance) you just built.

    ```shell
    docker run -it -v $PWD:/src/MLOS --name mlos-build mlos/build:ubuntu-20.0
    ```

3. Inside the container, [build the compiled software](../../../documentation/02-Build.md#cli-make) with `make`:

    ```sh
    make dotnet-build cmake-build
    ```

    > This will build everything using a default `CONFIGURATION=Release`.
    >
    > To just build `SmartCache` and `Mlos.Agent.Server`, execute the following: \
    > `make -C source/Examples/SmartCache && make -C source/Mlos.Agent.Server`

4. For a `Release` build (the default), the relevant output will be at:

    - Mlos.Agent.Server:

        `out/dotnet/source/Mlos.Agent.Server/obj/AnyCPU/Mlos.Agent.Server.dll`

    - SmartCache:

        `out/cmake/Release/source/Examples/SmartCache/SmartCache`

    - SmartCache.SettingsRegistry:

        `out/dotnet/source/Examples/SmartCache/SmartCache.SettingsRegistry/obj/AnyCPU/SmartCache.SettingsRegistry.dll`

## Executing

`SmartCache` can be invoked separate, or by the `Mlos.Agent.Server` itself.

Once started, `SmartCache` will attempt to register its component specific set of shared memory messages with the `Mlos.Agent` in the `Mlos.Agent.Server` using some `Mlos.Core` component registration messages.  That message includes the name of the `SettingsRegistry` assembly (`.dll`) corresponding to that component's settings/messages.

The `Mlos.Agent.Server` needs to be told where it can find those assemblies.  To do that we provide an `MLOS_SETTINGS_REGISTRY_PATH` environment variable.

In this case we populate it with the path to the `SmartCache.SettingsRegistry.dll`:

```sh
export MLOS_SETTINGS_REGISTRY_PATH="out/dotnet/source/Examples/SmartCache/SmartCache.SettingsRegistry/obj/AnyCPU:$MLOS_SETTINGS_REGISTRY_PATH"
```

Next, we can start the `Mlos.Server.Agent` using the `dotnet` command:

```sh
tools/bin/dotnet out/dotnet/source/Mlos.Agent.Server/obj/AnyCPU/Mlos.Agent.Server.dll
# Note: This is missing the .json file to connect to the optimizer service.
```

The `Mlos.Agent` that gets started will then wait for a signal that the component (`SmartCache`) has connected to the shared memory region before starting to poll the component for messages to process.

To start the `SmartCache` process we first need another shell instance in the docker container:

```sh
docker exec -it mlos-build /bin/bash
```

Now, we can start `SmartCache` as follows:

```sh
out/cmake/Release/source/Examples/SmartCache/SmartCache
```

> To have `Mlos.Agent.Server` start `SmartCache` without having to start another shell in the docker container instance, add the path to the `SmartCache` binary as an argument to the `dotnet ... Mlos.Agent.Server` invocation.

## Caveats

- The system currently only supports one shared memory region and doesn't cleanup the shared memory after itself.

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
