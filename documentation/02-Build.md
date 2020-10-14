# Build Instructions for MLOS

## Prerequisites

See [01-Prerequisites.md](./01-Prerequisites.md) for initial build tools setup instructions.

There are different instructions according to the environment setup you chose.

## Contents

- [Build Instructions for MLOS](#build-instructions-for-mlos)
  - [Prerequisites](#prerequisites)
  - [Contents](#contents)
  - [Docker](#docker)
    - [Create a new container instance](#create-a-new-container-instance)
      - [Using the upstream container image](#using-the-upstream-container-image)
      - [Using the locally built image](#using-the-locally-built-image)
    - [Other useful docker commands](#other-useful-docker-commands)
    - [Start an existing container instance](#start-an-existing-container-instance)
    - [Get a new shell in a running container instance](#get-a-new-shell-in-a-running-container-instance)
  - [Linux](#linux)
    - [CLI: `make`](#cli-make)
    - [VSCode](#vscode)
  - [Windows](#windows)
    - [CLI: `msbuild`](#cli-msbuild)
    - [Building with Visual Studio](#building-with-visual-studio)

## Docker

If you chose to use the Docker build environment and have already built or pulled a container image using the instructions in [01-Prerequisites.md](./01-Prerequisites.md#docker), then you can start an interactive session using the container image as follows:

### Create a new container instance

#### Using the upstream container image

```sh
docker run -it -v $PWD:/src/MLOS \
  --name mlos-build \
  ghcr.io/microsoft-cisl/mlos/mlos-build-ubuntu-20.04
```

#### Using the locally built image

```sh
# Run the image:
docker run -it -v $PWD:/src/MLOS \
  --name mlos-build \
  mlos-build-ubuntu-20.04
```

> Where `20.04` can also be replaced with another [supported `UbuntuVersion`](./01-Prerequisites.md#linux-distribution-requirements).
>
> Note: If you receive an error that the container name already exists, then you can use either the `docker rm` or `docker start` commands [below](#other-useful-docker-commands) to retry.
>
> The `-v $PWD:/src/MLOS` option makes the current directory (assumed to be the root of the MLOS repository) available inside the container so that you can edit the code from your host machine, but build it inside the container.
>
> Note that the build artifacts located at `out/` in the container are kept separate by default, so you can test with multiple containers at a time (e.g. each using different Ubuntu versions).
> You can use additional `-v /path/to/out-20.04:/src/MLOS/out` style arguments to direct that output to a host accessible locations if desired.

### Other useful docker commands

Here are some additional basic docker commands to help manage the container instance.

```sh
# List the MLOS related container instances
docker ps -a | grep -i mlos
```

```sh
# Gracefully stop the container instance
docker stop mlos-build
```

```sh
# Forcefully stop the container instance.
docker kill mlos-build
```

```sh
# Remove the container instance.
docker rm mlos-build
```

### Start an existing container instance

```sh
# Start the image if it already exists and was stopped:
docker start -i mlos-build
```

### Get a new shell in a running container instance

```sh
docker exec -it mlos-build /bin/bash
```

Once you have an interactive session in the container, the MLOS source code is available at `/src/MLOS` and can be built using the same instructions in the [Linux: CLI `make`](#cli-make) section below.

## Linux

### CLI: `make`

We provide `Makefile` wrappers to invoke the language specific build systems.

```sh
make
```

> This is equivalent to `make dotnet-build cmake-build`

If you want to switch to a debug build run:

```sh
export CONFIGURATION=Debug
make
```

> Note: `export CONFIGURATION=Release` to switch back to `Release` builds.

The `Makefile`s in most source folders are simply wrappers around the `cmake` build system and allow easier interactive building during development without having to maintain shell environment variables or additional paths.

In general `cmake` is used for C++ projects, with simple `CMakeLists.txt` wrappers around `dotnet build` for their C# dependencies to do code generation.

In top-level directories you can restrict the build to just `dotnet` wrappers or just `cmake` wrappers like so:

```sh
make dotnet-build
make dotnet-test
make dotnet-clean

make cmake-build
make cmake-test
make cmake-clean
```

> Note: A similar shell environment setup can optionally be obtained with the following
>
> ```sh
> source ./scripts/init.linux.sh
> ```

To build *and* run the tests below the current directory run

```sh
make check
```

> This is equivalent to `make all test`

### VSCode

TODO

## Windows

For the C++ and C# project components, Visual Studio `msbuild` can be used on Windows systems.

> Note: Visual Studio build tools are available free. \
> Please see the initial setup instructions linked [above](#prerequisites) for details.

### CLI: `msbuild`

To build from the command line on Windows, the Visual Studio build tools need to be added to the shell environment.

1) Setup the `powershell` environment to find the Visual Studio build tools.

    ```powershell
    .\scripts\init.windows.ps1
    ```

    > Note: you can also execute `.\scripts\init.windows.cmd` if you prefer a `cmd` environment.

2) Use `msbuild` to build the project file in the current directory.

   > e.g. when run from the root of the MLOS repo this will recursively build all the projects and run the tests.

    ```shell
    msbuild /m /r /p:Configuration=Release
    ```

    Some additional build flags to help provide additional control over the process:

      - `/m` runs a multi-process parallel build process
      - `/r` is required on first build and git pull to *restore* any nuget packages required \
      - `/fl` will optionally produce a msbuild.log file
      - `/p:Configuration=Release` will perform a non-debug build.
        > Note: If omitted, `msbuild` will produce a Debug build by default.  Debug builds perform no compiler optimizations, so are useful for troubleshooting, but will be more difficult for MLOS to help optimize.
      - `/p:RunUnitTest=false` will temporarily skip running unit tests
      - `/p:StyleCopEnabled=false` will temporarily skip C# style checks
      - `/p:UncrustifyEnabled=false` will temporarily skip C++ style checks
      - `/p:BuildProjectReferences=false` will temporarily only build the current project file, and skip rebuilding its dependencies
        (note: this option doesn't work when building `.sln` files)

### Building with Visual Studio

> Note: Visual Studio 2019 Community Edition is available free. \
> Please see the initial setup instructions linked [above](#prerequisites) for details.

Opening a `*.sln` file in the `source/` directory with Visual Studio 2019 should allow you to build inside the IDE.

1) Setup the shell environment to find the `devenv` script provided by Visual Studio.

    ```powershell
    .\scripts\init.windows.ps1
    ```

    > Note: you can also execute `.\scripts\init.windows.cmd` if you prefer a `cmd` environment.

2) Launch Visual Studio for a given solution:

    ```shell
    devenv Mlos.NetCore.sln
    ```

    Alternatively, you can launch `devenv` for a project and manually add its dependencies to the solution that Visual Studio creates.
    For instance:

    ```shell
    devenv Mlos.Core.vcxproj
    ```
