# MLOS: Machine Learning Optimized Systems

## MLOS: An Infrastructure for Automated Software Performance Engineering

> MLOS is an ML-powered infrastructure and methodology to democratize and automate Performance Engineering. MLOS enables continuous, instance-based, robust, and trackable systems optimization.

From the [MLOS paper at DEEM 2020](https://arxiv.org/abs/2006.02155)

## Overview

### Problem

All systems software (e.g. SqlServer, MySQL, LevelDB, OpenSSL, etc.) is full of parameter choices.

Sometimes these are encoded in the software as constants embedded in the code (e.g. choice of abstract data structure implementation, buffer limit size or alignment, etc.).
Other times they may be exposed as configuration parameters either at startup or runtime.

Careful selection of these parameters can yield dramatic performance differences for different _contexts_ of a system (e.g. different workloads, hardware, etc.).
Note that _performance_ can be interpreted in different ways (e.g. reducing average/variability of latency/memory, increasing throughput, decreasing MTTR, etc.)

Generally speaking, this process is referred to as *Software Performance Engineering*, and typically involves a lot of manual effort that is brittle and not well tracked.

### Goals

MLOS is about using machine-learning and data-science to optimize systems for a given context through these tunable choices.

![MLOS data science experience for software performance engineering](./documentation/images/MLOS-Experience.png)

Roughly, this can happen in two modes:

1. Offline (e.g. at development time)

    In this case, developers can use (micro)benchmarks to explore a parameter space for a component either interactively or with a background CI/CD pipeline and then interact with that data through a notebook experience to select the right value to check in to the code, along with the results of the experiments and analysis, all encoded in the notebook.

2. Online (e.g. at runtime)

    In this case a system component provides hooks to adjust its parameters at runtime and exports data about its current state/performance.  These can be combined with additional contextual information from the system to build a model (or simple heuristics) to invoke the hooks to adjust the component to improve performance at runtime.

### Architecture

![MLOS architecture overview](./documentation/images/MLOS-Architecture.png)

To achieve this MLOS provides:

1. *Code Annotations* to help describe additional *settings metadata* for tunables (a.k.a. `Settings`).

    For instance, metadata can include things like constraints on acceptable values a Setting can take on as well as developer intuition to help guide the automated search process.

    Currently these are implemented as C# Attributes to provide reflection and easy cross-platform and cross-compiler support for C++ projects.

2. *Code Generation* tools to use that metadata to expose those settings to different target systems/languages (e.g. Python Notebooks, C++, C#, etc.)

    For instance, we generate efficient messages over shared memory communication channels for

    1. exporting data about the component using that Setting

        For instance, this may include performance statistics, workload traces, etc.

    2. receiving feedback (e.g. to change the Setting's value)

        This may involve a reconfiguration step or simply update a cache for the next instantiation to read.

3. An external agent (`Mlos.Agent.Server`) which can consume the information exported by the target system (e.g. SqlServer, MySQL, LevelDB, etc.) with mimimal impact on the target system.

    The external agent can perform workload summarization, binning, cataloging, model inference, heuristic invocation, etc. based on the events exposed by the target system to then influence it.

    Once hooks are created in the target system, iteration on the external agent can be more rapidly developed and deployed.

## Python quickstart
The easiest way to get started with MLOS is to just the Python package.
You can find installation instructions in the [Prerequisites: Python Quickstart](./documentation/01-Prerequisites.md#python-quickstart).


## Full Build (C# and C++ components)

MLOS supports Windows and Linux build environments.

For detailed instructions, please refer to:

  1. [Prerequisites](./documentation/01-Prerequisites.md)
  2. [Build](./documentation/02-Build.md)

## Examples

Code and documentation for examples of using MLOS to optimize a system are described in the [Notebooks](https://microsoft.github.io/MLOS/notebooks/) section.
Additional code is in the  [source/Examples](./source/Examples/#mlos-github-tree-view) source directory.
You can find the source of the notebooks [on github as well](./source/Mlos.Notebooks/#mlos-github-tree-view).

## Documentation

- Additional overview documentation is available in the [documentation](./documentation/) tree.

- Individual components may also include more detailed documentation in their respective subdirectories.

## Contributing

We welcome contributions!  Please see [Contributing](./CONTRIBUTING.md) and [Code of Conduct](./CODE_OF_CONDUCT.md) for details.

Also, please see the [Roadmap](#) of planned features.

## Contact

For more formal enquiries, you can [contact us](mailto:mlos-maintainers@service.microsoft.com).

## License

- [MIT License](./LICENSE.txt)
