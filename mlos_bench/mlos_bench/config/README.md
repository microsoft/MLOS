# `config` Examples Overview

The [`config`](./../config/) directory contains a collection of scripts and config snippets that are used to configure the `mlos_bench` components.

These are meant to be used as examples and starting points for your own configuration, though some can be included as-is in your configuration (e.g. linux kernel configs).

In general the `config` directory layout follows that of the `mlos_bench` module/directory layout (e.g. `remote` and `local` `environments` making using of `services`, etc., each with their own `json` configs and shell scripts.).

Full end-to-end examples are provided in the [`environments/composite`](./environments/composite/) directory, and make use of the `CompositeEnvironment` to combine multiple `environments` and `services` into a single `mlos_bench` run.
