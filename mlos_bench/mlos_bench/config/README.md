# `config` Examples Overview

The [`config`](./) directory contains a collection of scripts and config snippets that are used to configure the `mlos_bench` components.

These are meant to be used as examples and starting points for your own configuration, though some can be included as-is in your configuration (e.g. linux kernel configs).

In general the `config` directory layout follows that of the `mlos_bench` module/directory layout (e.g. `remote` and `local` `Environments` making using of `Services`, etc., each with their own `json` configs and shell scripts.).

Full end-to-end examples are provided in the [`cli`](./cli/) directory, and typically and make use of the root [`CompositeEnvironments`](./environments/root/) to combine multiple [`Environments`](./environments/), also referencing [`Services`](./services/), [`Storage`](./storage/), and [`Optimizer`](./optimizers/) configs, into a single [`mlos_bench`](../run.py) run.

## Globals

As mentioned in the [mlos_bench/README.md](../../README.md),
a general rule is that the parameters from the global configs like `global_config_azure.json` or `experiment_MyAppBench.jsonc` override the corresponding parameters in other configurations.
That allows us to propagate the values of the parameters that are specific to the experiment into other components of the framework and keep the majority of the config files in our library immutable and reusable.

## Schemas

The [`schemas`](./schemas/) directory contains the [`jsonschema`](https://json-schema.org/) schemas for the `mlos_bench` config files and may also be helpful when writing your own configs.

For instance including a `"$schema"` attribute at the top of your `json` config file will enable `json` validation and auto-complete in many editors (e.g. [VSCode](https://code.visualstudio.com/)):

```jsonc
{
    "$schema": "https://raw.githubusercontent.com/microsoft/MLOS/main/mlos_bench/mlos_bench/config/schemas/environments/environment-schema.json",


    "class": "mlos_bench.environments.SomeEnviroment",
    "config": {
        // ...
    }
}
```
