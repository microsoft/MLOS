# Test Instructions for MLOS

## Contents

- [Test Instructions for MLOS](#test-instructions-for-mlos)
  - [Contents](#contents)
  - [Linux Tests](#linux-tests)
    - [Run C# Tests on Linux](#run-c-tests-on-linux)
    - [Run C++ Tests on Linux](#run-c-tests-on-linux-1)
    - [Run Python Tests on Linux](#run-python-tests-on-linux)
  - [Windows](#windows)
    - [Run C#/C++ Tests on Windows](#run-cc-tests-on-windows)
    - [Run Python Tests on Windows](#run-python-tests-on-windows)

## Linux Tests

To build and test all of the MLOS code at or below the current folder, regardless of language, run:

```sh
make check
```

> That is equivalent to `make all test`

To only invoke the tests run (not re-check the build):

```sh
make test
```

See below for additional targets to restrict the languages invoked:

### Run C# Tests on Linux

From any source directory, running the following should invoke `dotnet build` and `dotnet test` recursively for any projects in that folder or below it:

```sh
make dotnet-test
```

### Run C++ Tests on Linux

From any source directory, running the following should invoke approprite `cmake` and `ctest` commands to build and test projects recursively in that folder or below it:

```sh
make cmake-build cmake-test
```

### Run Python Tests on Linux

First, ensure that the necessary Python modules are installed.
See [01-Prerequisites.md](./01-Prerequisites.md#linux-python-install) for details.

From the root of MLOS source tree:

```sh
make python-tests
```

invokes `scripts/run-python-tests.sh` to run the Python unit tests.

## Windows

### Run C#/C++ Tests on Windows

As mentioned in [02-Build.md](02-Build.md#msbuild-cli), invoking `msbuild` from the `tests/` directory will invoke the `C++` and `C#` tests unless the `RunUnitTest` property is set to `false`.

On Windows, to build and run the tests for both C++ and C#:

```powershell
cd test/
msbuild /m /r /p:RunUnitTest=true
```

> Note: Generally `RunUnitTest` will default to `true` when left unspecified.

To only run the tests and not recheck the build:

```powershell
msbuild /p:RunUnitTest=true /p:BuildProjectReferences=false
```

### Run Python Tests on Windows

First, ensure that the necessary Python modules are installed.
See [01-Prerequisites.md](./01-Prerequisites.md#windows-python-install) for details.

```cmd
scripts\run-python-tests.cmd
```
