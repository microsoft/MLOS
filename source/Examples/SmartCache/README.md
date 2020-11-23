# [SmartCache Example](./#mlos-github-tree-view)

This [`SmartCache`](./#mlos-github-tree-view) example is a C++ implementation of the [Python SmartCache](../../Mlos.Python/mlos/Examples/SmartCache/#mlos-github-tree-view).

It implements a simple cache with different replacement policies and cache size as built-in tunables and some simple workloads.

It can be used to demonstrate a full end-to-end MLOS integrated microbenchmark for a "smart" component (in this case a cache).

## Contents

- [SmartCache Example](#smartcache-example)
  - [Contents](#contents)
  - [Building](#building)
    - [Linux](#linux)
    - [Windows](#windows)
  - [Executing](#executing)
    - [Without an optimizer](#without-an-optimizer)
      - [Linux](#linux-1)
      - [Windows](#windows-1)
      - [Example output](#example-output)
    - [With an optimizer](#with-an-optimizer)
      - [Example output](#example-output-1)
  - [Explanation](#explanation)
  - [See Also](#see-also)

## Building

See Also

- General [build](../../../documentation/02-Build.md) instructions

> Note: these commands are given relative to the root of the MLOS repo.

### Linux

> You can [pull or build the Docker image](../../../documentation/01-Prerequisites.md#build-the-docker-image) using the
> [`Dockerfile`](../../../Dockerfile#mlos-github-tree-view) at the root of the repository to get a Linux build environment.

```sh
make -C source/Mlos.Agent.Server
make -C source/Examples/SmartCache all install
```

> The `install` target places the output in the more convenient `target/bin/...` path.

### Windows

```cmd
msbuild /m /r source/Mlos.Agent.Server/Mlos.Agent.Server.csproj
msbuild /m /r source/Examples/SmartCache/SmartCache.vcxproj
```

## Executing

### Without an optimizer

#### Linux

```sh
dotnet target/bin/Release/Mlos.Agent.Server.dll \
    --settings-registry-path target/bin/Release/AnyCPU \
    --experiment target/bin/Release/AnyCPU/SmartCache.ExperimentSession/SmartCache.ExperimentSession.dll \
    --executable target/bin/Release/x86_64/SmartCache
```

#### Windows

```cmd
dotnet target/bin/Release/Mlos.Agent.Server.dll \
    --settings-registry-path target/bin/Release/AnyCPU \
    --experiment target/bin/Release/AnyCPU/SmartCache.ExperimentSession/SmartCache.ExperimentSession.dll \
    --executable target/bin/Release/x64/SmartCache.exe
```

#### Example output

```txt
Mlos.Agent.Server
Starting target/bin/Release/x86_64/SmartCache
observations: 0
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

### With an optimizer

The examples above merely communicate the SmartCache's progress with the external agent using shared memory.

To also have the SmartCache tune itself by connecting to an optimizer we need to

1. Start an optimizer:

    ```shell
    start_optimizer_microservice launch --port 50051
    ```

    > This assumes that the `mlos` module has already been installed and is available on the command search `PATH` environment variable.
    >
    > See the [Python Quickstart documentation](../../../documentation/01-Prerequisites.md#python-quickstart) for details.

2. Add `--optimizer-uri http://localhost:50051` to the set of arguments to the command above.

#### Example output

```sh
dotnet target/bin/Release/AnyCPU/Mlos.Agent.Server/Mlos.Agent.Server.dll \
    --executable target/bin/Release/x86_64/SmartCache \
    --settings-registry-path target/bin/Release/AnyCPU \
    --experiment target/bin/Release/AnyCPU/SmartCache.ExperimentSession/SmartCache.ExperimentSession.dll \
    --optimizer-uri http://localhost:50051

```txt
Mlos.Agent.Server
Connecting to the Mlos.Optimizer
Starting target/bin/Release/x86_64/SmartCache
observations: 0
info: Microsoft.Hosting.Lifetime[0]
      Now listening on: http://[::]:5000
info: Microsoft.Hosting.Lifetime[0]
      Application started. Press Ctrl+C to shut down.
info: Microsoft.Hosting.Lifetime[0]
      Hosting environment: Production
info: Microsoft.Hosting.Lifetime[0]
      Content root path: /src/MLOS
Starting Mlos.Agent
Waiting for Mlos.Agent to exit
Found settings registry assembly at target/bin/Release/AnyCPU/SmartCache.SettingsRegistry.dll
Waiting for agent to respond with a new configuration.
Register {
  "cache_implementation": "LeastRecentlyUsed",
  "lru_cache_config.cache_size": 100
} HitRate = 0
Suggest False {"cache_implementation": "LeastRecentlyUsed", "lru_cache_config.cache_size": 747}
observations: 1
Waiting for agent to respond with a new configuration.
Register {
  "cache_implementation": "LeastRecentlyUsed",
  "lru_cache_config.cache_size": 747
} HitRate = 0
Suggest False {"cache_implementation": "MostRecentlyUsed", "mru_cache_config.cache_size": 2554}
observations: 2
...
```

## Explanation

The `Mlos.Agent` that gets started by the `Mlos.Agent.Server` waits for a signal that the component (`SmartCache`) has connected to the shared memory region before starting to poll the component for messages to process.
This is important in case the component is started independently.

In this case, `Mlos.Agent.Server` itself starts the component.

Once started, `SmartCache` will attempt to register its component specific set of shared memory messages with the `Mlos.Agent` in the `Mlos.Agent.Server` using `RegisterComponentConfig` and `RegisterAssemblyRequestMessage` from `Mlos.Core` and `Mlos.NetCore`.
That includes the name of the `SettingsRegistry` assembly (`.dll`) corresponding to that component's settings/messages.

The `Mlos.Agent.Server` needs to be told where it can find those assemblies in order to load them so that it can parse the messages sent by the component.
To do that, we use the `--settings-registry-path` option.
We also need to provide the path to a corresponding `ExperimentSession` dll in the `--experiment` option in order to tell the agent how to process those messages for this experiment.

In the second example we also tell the `Mlos.Agent.Server` how to connect to the (Python) MLOS Optimizer Service over GRPC so that the application message handlers setup by the `SmartCache.SettingsRegistry` for the agent can request new configuration recommendations on behalf of the application.

For additional details, see:

- [Mlos.Agent.Server/MlosAgentServer.cs](../../Mlos.Agent.Server/MlosAgentServer.cs#mlos-github-tree-view)
- [SmartCache/Main.cpp](./Main.cpp#mlos-github-tree-view)
- [SmartCache.ExperimentSession/SmartCacheExperimentSession.cs](./SmartCache.ExperimentSession/SmartCacheExperimentSession.cs#mlos-github-tree-view)
- [SmartCache.SettingsRegistry/Codegen/SmartCache.cs](./SmartCache.SettingsRegistry/Codegen/SmartCache.cs#mlos-github-tree-view)

## See Also

For additional implementation details and demonstration code, please see the [SmartCache CPP Notebook](https://microsoft.github.io/MLOS/notebooks/SmartCacheCPP)
