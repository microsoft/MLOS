# Experiment-specific parameters

Some global parameters vary from experiment to experiment.
It makes sense to store them in a separate file and include it in the `"globals"` section of the CLI config - or, better yet, specify it in the `--globals` option in the command line.
Just like with other global configs, the values from the experiment configuration will override the corresponding values in the Environment, Service, Optimizer, and Storage configs down the configuration tree.
This way we can keep most of our configs immutable and reusable across different experiments and system configurations.

## Working example

Let's take a look at the [`experiment_RedisBench.jsonc`](experiment_RedisBench.jsonc) file.
it looks like this:

```jsonc
{
    // The name of the experiment.
    // This is required value and should be unique across incompatible experiments
    // (e.g., those with differing tunables, scripts, versions, etc.), since it also
    // controls how trial data is stored and reloaded to resume and repopulate the
    // optimizer state.
    "experiment_id": "RedisBench",

    "deploymentName": "RedisBench",
    "vmName": "os-autotune-linux-vm",

    "resourceGroup": "os-autotune",
    "location": "westus2",

    "virtualNetworkName": "mlos-2vms-vnet",
    "subnetName": "mlos-2vms-subnet",

    "storageAccountName": "osatsharedstorage",
    "storageFileShareName": "os-autotune-file-share",

    "vmSize": "Standard_B2s",
    "ubuntuOSVersion": "18.04-LTS",

    "tunable_params_map": {

        // VM provisioning parameter groups (see `azure-vm-tunables.jsonc`):
        // ["azure-vm"] (not used at the moment)
        "provision": [],

        // Boot-time Linux parameter groups (see `linux-boot-tunables.jsonc`):
        // ["linux-kernel-boot"]
        "linux-boot": ["linux-kernel-boot"],

        // Runtime Linux parameter groups (see `linux-runtime-tunables.jsonc`):
        // ["linux-swap", "linux-hugepages-2048kB", "linux-scheduler"]
        "linux-runtime": ["linux-swap", "linux-scheduler"],

        // Redis config parameter groups (see `redis-tunables.jsonc`):
        // ["redis"]
        "redis": []
    },

    "optimization_target": "score",
    "optimization_direction": "min"
}
```

It has a mixture of parameters from different components of the framework. for example, the following section contains the parameters that are specific to the Azure VM provisioning:

```jsonc
{
    "resourceGroup": "os-autotune",
    "location": "westus2",

    "virtualNetworkName": "mlos-2vms-vnet",
    "subnetName": "mlos-2vms-subnet",

    "storageAccountName": "osatsharedstorage",
    "storageFileShareName": "os-autotune-file-share",

    "vmSize": "Standard_B2s",
    "ubuntuOSVersion": "18.04-LTS"
}
```

At runtime, these values will be pushed down to the `AzureVMService` configuration, e.g., [`service-linux-vm-ops.jsonc`](../services/remote/azure/service-linux-vm-ops.jsonc).

Likewise, parameters

```jsonc
{
    "optimization_target": "score",
    "optimization_direction": "min"
}
```

will be pushed down to the `Optimizer` configuration, e.g., [`mlos_core_flaml.jsonc`](../optimizers/mlos_core_flaml.jsonc), and so on.

> NOTE: it is perfectly ok to have several files with the experiment-specific parameters (say, one for Azure, another one for Storage, and so on) and either include them in the `"globals"` section of the CLI config, and/or specify them in the command line when running the experiment, e.g.
>
> ```bash
> mlos_bench --config mlos_bench/mlos_bench/config/cli/azure-redis-opt.jsonc --globals experiment_Redis_Azure.jsonc experiment_Redis_Tunables.jsonc --max_iterations 10
> ```
>
> (Note several files after the `--globals` option).

### Tunable Parameters Map

The `"tunable_params_map"` section is a bit more interesting.
It allows us to specify which tunable parameters we want to optimize for.
Values on the right side of the mapping correspond to the names of the covariant tunable groups, e.g., `"linux-swap"` or `"linux-scheduler"` in [`linux-runtime-tunables.jsonc`](../environments/os/linux/runtime/linux-runtime-tunables.jsonc).
Identifiers on the left side, e.g., `"linux-runtime"`, are arbitrary and are used as a reference to the corresponding covariant tunable groups.
We can use those identifiers inside the `"tunable_params"` section of the Environment configs to specify which tunable parameters we want to optimize for.
We use a `$` prefix to distinguish such identifiers from the actual names of the covariant groups.
In the Environment config, it will look like the following:

```jsonc
{
    "name": "Generate Linux kernel parameters for Ubuntu",
    "class": "mlos_bench.environments.LocalFileShareEnv",

    "config": {

        "tunable_params": ["$linux-runtime"],

        // ...
    }
}
```

If there are several dollar variables in the `"tunable_params"` section, they will get concatenated into a single list of covariant groups identifiers.

This way, we can enable and disable optimization for certain parameters in the top-level experiment config and keep the leaf Environment configs immutable and reusable across different experiments and system configurations.
