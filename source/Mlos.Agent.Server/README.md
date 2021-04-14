# Mlos.Agent.Server

## Contents

- [Mlos.Agent.Server](#mlosagentserver)
  - [Contents](#contents)
  - [Overview](#overview)
  - [Building](#building)
    - [Linux](#linux)
    - [Windows](#windows)
  - [Executing](#executing)
  - [Caveats](#caveats)

## Overview

The [`Mlos.Agent.Server`](./#mlos-github-tree-view) is essentially a small and generic C# wrapper around several other communication channels to allow different components to connect for component experimentation convenience.

It provides

1. Shared memory communication channels via the [`Mlos.Agent`](../Mlos.Agent/#mlos-github-tree-view) and [`Mlos.NetCore`](../Mlos.NetCore/#mlos-github-tree-view) libraries.

2. A [`Mlos.Agent.GrpcServer`](../Mlos.Agent.GrpcClient/#mlos-github-tree-view) GRPC channel to allow driving the experimentation process from a Jupyter notebook (work in progress).

3. A GRPC client to allow connecting to the (Python) [`mlos.Grpc.OptimizerServicesServer`](../Mlos.Python/mlos/Grpc/OptimizerServicesServer.py#mlos-github-tree-view) to store and track those experiments.

Since it is meant as a reusable agent for different components, it contains no specific message processing logic itself.

Rather, it starts an [`Mlos.Agent`](../Mlos.Agent/#mlos-github-tree-view) message processing loop which loads each component's `SettingsRegistry` assembly dlls upon registration request (via the `RegisterComponentConfig` and `RegisterAssemblyRequestMessage` from [`Mlos.Core`](../Mlos.Core/#mlos-github-tree-view) and [`Mlos.NetCore`](../Mlos.NetCore/#mlos-github-tree-view)) and uses the specified `ExperimentSession` class to setup the message callbacks that handle compnent and experiment specific things like aggregating and summarizing telemetry messages, interfacing with the optimizer using different parameter and/or context search spaces, and relaying component reconfiguration requests, etc.

See the [`SmartCache`](../Examples/SmartCache/#mlos-github-tree-view) code, especially its [`ExperimentSession` class](../Examples/SmartCache/SmartCache.ExperimentSession/SmartCacheExperimentSession.cs#mlos-github-tree-view) for a more detailed example.

## Building

See Also

- General [build](../../documentation/02-Build.md) instructions

> Note: these commands are given relative to the root of the MLOS repo.

### Linux

```sh
make -C source/Mlos.Agent.Server
```

### Windows

```cmd
msbuild /m /r source/Mlos.Agent.Server/Mlos.Agent.Server.csproj
```

## Executing

The `Mlos.Agent.Server` has several different operating modes.
Please see the `--help` usage output for additional details.

```shell
dotnet target/bin/Release/Mlos.Agent.Server.dll --help
```

## Caveats

- The system currently only supports a single tunable process at a time.
  Multiple agent/target-process pairs support (e.g. via configurable unix socket domain path for anonymous shared memory exchange) are planned for future development.

