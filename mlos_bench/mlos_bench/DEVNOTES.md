# Notes to the developer

This document is a developer's perspective of the `mlos_bench` framework.
It is work in progress; we will keep extending it as we develop the code.

## Environment

At the center of the `mlos_bench` framework is the `Environment` class.
The environment implement the `.setup()`, `.run()`, and `.teardown()` stages of a trial, and also encapsulates the configuration and the tunable parameters of the benchmarking environment.

For most of the use cases, there is no need to implement custom `Environment` classes, as `mlos_bench` already has a library of ready to use `Environment` implementations, e.g., for running setup/run/teardown scripts locally or on the remote host.

At runtime, `mlos_bench` instantiates the `Environment` objects from config files.
Each `Environment` config is a JSON5 file with the following structure:

```javascript
{
    "name": "Mock environment",  // Environment name / ID
    "class": "mlos_bench.environments.mock_env.MockEnv",  // A class to instantiate

    "config": {
        "tunable_params": [
            // Groups of variable parameters passed to .setup() on each trial
            // (e.g., suggested by the optimizer):
            "linux-kernel-boot",
            "linux-scheduler",
            "linux-swap",
            // ...
        ],
        "const_args": {
            // Additional .setup() parameters that do not change from trial to trial:
            "foo": "bar",
            // ...
        }
        // Environment constructor parameters
        // (specific to the Environment class being instantiated):
        "seed": 42,
        // ...
    }
}
```

### `const_args` and `tunable_params`

Note that in the config above we have three groups of parameters.
`tunable_params` are the configuration parameters that are passed to the `.setup()` call on each trial.
They are external to the environment, and are usually either suggested by the optimizer, or specified explicitly by the user (e.g., when benchmarking a certain configuration).
`const_args` is a loose collection of key/value pairs that complement the `tunable_params` values.
These values do not change from one trial to the next (though could change from one `mlos_bench` `run.py` to another via environment variable consumption), but they also appear as input parameters for each `Environment.setup()` call to use in their `setup` and `run` scripts, for instance.
Other config parameters, like `seed`, are class-specific and appear as the constructor arguments during the class instantiation.

## Service

Some functionality is shared across several environments, so it makes sense to factor it out in separate classes and configs.
Environments can include configs for the `Service` classes, and access the methods of the services internally.
`Service` classes provide generic APIs to certain cloud functionality; e.g., an `AzureVMService` for provisioning and managing VMs on Azure can have a drop-in replacement for the analogous functionality on AWS, etc.
