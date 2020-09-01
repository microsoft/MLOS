# Repo Organization

Some notes on the directory layout organization in this repo.

- There are build files (e.g. `dirs.proj` for `msbuild` or `dotnet build`, or `Makefile`s for `make`) in most directories to allow easy recursive building of that subtree you happen to be in.
  > Note: we provide `Makefile` wrappers in most directories to simply help invoke `cmake` and the `Makefiles` it generates
- [`build/`](../build) contains configuration related to building MLOS components
  - For instance, `.props` and `.targets` files for definining and controlling common `msbuild` and `dotnet build` properites and targets are contained there, as are various style check configurations.
  > Note: For this reason, `cmake` output is redirected to `out/cmake/{Release,Debug}/` instead.
- [`source/`](../source) contains a directory for each component of MLOS, including unit test source code.
  - i.e. running `msbuild` or `make` in the `source/` directory will build (and generally analyze) all of the projects, but not execute their tests.
  - [`source/Examples/`](../source/Examples) contains sample target codes to optimize with the other MLOS components and help describe the integration methods
  - [`source/Mlos.Notebooks/StartHere.ipynb`](../source/Mlos.Notebooks/StartHere.ipynb) contains a sample Notebook with a basic MLOS optimization walkthrough
- [`test/`](../test) contains a directory and project to invoke each of the unit tests.
  - i.e. running `msbuild` or `make` in the `test/` directory will also run all of the tests.
- [`scripts/`](../scripts) contains some helper scripts to initialize development environments, install tools, invoke build pipelines, etc.

Auto generated content:

- `out/` contains most of the intermediate build output, especially for `msbuild` and `dotnet build` portions
  - `out/dotnet` contains the `msbuild` and `dotnet build` outputs (for Windows)
  - `out/Mlos.CodeGen.out` contains code generation output from each `SettingsRegistry` project, organized by originating `source/` project directory
  - `out/Grpc.out` contains the output for the grpc messages between the `Mlos.Agent`s
- `target/` contains final binaries and libraries produced by `msbuild` that are suitable for execution
- `out/cmake/` contains most of the output from `cmake`
  > Note: this is by convention.  Though we provide some configurations to help use this path, other tools or IDEs may override it.
- `tools/` is created for items the `cake` build scripts may fetch
