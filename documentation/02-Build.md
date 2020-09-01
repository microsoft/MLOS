# Build Instructions for MLOS

## Prerequisites

See [01-Prerequisites.md](./01-Prerequisites.md) for initial build tools setup instructions.

## Contents

- [Build Instructions for MLOS](#build-instructions-for-mlos)
  - [Prerequisites](#prerequisites)
  - [Contents](#contents)
  - [Docker](#docker)
  - [Linux](#linux)
    - [CLI](#cli)
    - [VSCode](#vscode)
  - [Windows](#windows)
    - [CLI](#cli-1)
    - [Visual Studio](#visual-studio)

## Docker

Assuming you've built a container image using the instructions in [01-Prerequisites.md](./01-Prerequisites.md#docker) you can start an interactive session using the container image as follows:

```sh
# Using the UbuntuVersion local shell variable set earlier to "docker build" the image:
UbuntuVersion=20.04
# Run the image:
docker run -it -v $PWD:/src/MLOS \
  --name mlos-build-$UbuntuVersion \
  mlos/build:ubuntu-$UbuntuVersion
```

> The `-v $PWD:/src/MLOS` option makes the current directory (assumed to be the root of the MLOS repository) available inside the container so that you can edit the code from your host machine, but build it inside the container.

> Note that the build artifacts located at `out/` in the container are kept separate by default, so you can test with multiple containers at a time.
> You can use additional `-v /path/to/out-$UbuntuVersion:/src/MLOS/out` style arguments to direct that output to a host accessible locations if desired.

```sh
# Start the image if it already exists and was stopped:
docker start -i mlos-build-$UbuntuVersion
```

```sh
# Start a new shell session inside the image:
docker exec -it mlos-build-$UbuntuVersion /bin/bash
```

Once you have an interactive session in the container, the MLOS source code is available at `/src/MLOS` and can be built using the same instructions in the [Linux CLI](#cli) section below.

## Linux

### CLI

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

TODO: Provide some notes about how cmake integration works with vscode.

## Windows

For the C++ and C# project components, Visual Studio `msbuild` can be used on Windows systems.

> Note: Visual Studio build tools are available free. \
> Please see the initial setup instructions linked [above](#prerequisites) for details.

### CLI

Visual Studio build tools need to be added to the shell environment.

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

### Visual Studio

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
    devenv MLOS.NetCore.sln
    ```

    Alternatively, you can launch `devenv` for a project and manually add its dependencies to the solution that Visual Studio creates.
    For instance:

    ```shell
    devenv MLOS.Core.vcxproj
    ```
