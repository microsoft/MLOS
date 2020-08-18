# Build Instructions for MLOS

## Prerequisites

See [01-Prerequisites.md](./01-Prerequisites.md) for initial build tools setup instructions.

## Linux

TODO

## Windows

### CLI

Visual Studio build tools need to be added to the shell environment.

> Note: Visual Studio build tools are available free. \
> Please see the initial setup instructions linked [above](#prerequisites) for details.

1) Setup the `powershell` environment to find the Visual Studio build tools.

    ```powershell
    .\scripts\init.windows.ps1
    ```

    > Note: you can also execute `.\scripts\init.windows.cmd` if you prefer a `cmd` environment.

2) Use `msbuild` to build the project file in the current directory.

   > e.g. when run from the root of the MLOS repo this will recursively build all the projects and run the tests.

    ```shell
    msbuild /m /r
    ```

    Some additional build flags to help provide additional control over the process:

      - `/m` runs a multi-process parallel build process
      - `/r` is required on first build and git pull to *restore* any nuget packages required \
      - `/fl` will optionally produce a msbuild.log file
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
