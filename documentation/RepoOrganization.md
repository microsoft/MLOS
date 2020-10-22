# Repo Organization

Some notes on the directory layout organization in this repo.

- There are build files (e.g. `dirs.proj` for `msbuild` or `dotnet build`, or `Makefile`s for `make`) in most directories to allow easy recursive building of that subtree you happen to be in.
  > Note: we provide `Makefile` wrappers in most directories to simply help invoke `cmake` and the `Makefiles` it generates
- [`build/`](../build/#mlos-github-tree-view) contains configuration related to building MLOS components
  - For instance, `.props` and `.targets` files for definining and controlling common `msbuild` and `dotnet build` properties and targets are contained there, as are various style check configurations.
  > Note: For this reason, `cmake` output is redirected to `out/cmake/{Release,Debug}/` instead.
- [`source/`](../source/#mlos-github-tree-view) contains a directory for each component of MLOS, including unit test source code.
  - i.e. running `msbuild` or `make` in the `source/` directory will build (and generally analyze) all of the projects, but not necessarily execute their tests.

  - Many components include more detailed documentation about their implementation internals.

    For instance:

    - [Mlos Settings System Code Generation System](../source/Mlos.SettingsSystem.CodeGen/)
    - [Mlos.Core Shared Memory Communication Channel](../source/Mlos.Core/doc/)

  - [`source/Examples/`](../source/Examples/) contains sample target codes to optimize with the other MLOS components and help describe the integration methods

    For instance:

    - [Smart Cache C++](../source/Examples/SmartCache/)

- [`test/`](../test/#mlos-github-tree-view) contains a directory and project to invoke each of the unit tests.
  - i.e. running `msbuild` or `make` in the `test/` directory will also run all of the tests.
- [`scripts/`](../scripts/#mlos-github-tree-view) contains some helper scripts to initialize development environments, install tools, invoke build pipelines, run tests, etc.

Auto generated content:

- `out/` contains most of the intermediate build output, especially for `msbuild` and `dotnet build` portions
  - `out/dotnet` contains the `msbuild` and `dotnet build` outputs (for Windows)
  - `out/Mlos.CodeGen.out` contains code generation output from each `SettingsRegistry` project, organized by originating `source/` project directory
  - `out/Grpc.out` contains the output for the grpc messages between the `Mlos.Agent`s
- `target/` contains final binaries and libraries produced by `msbuild` and `make install` that are suitable for execution
- `out/cmake/{Release,Debug}/` contains most of the output from `cmake`
  > Note: this is by convention.  Though we provide some configurations to help use this path, other tools or IDEs may override it or may need to be configured to work with it.
- `tools/` is where local versions of `dotnet`, `cmake`, and `cake` are fetched and installed.
