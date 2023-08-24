# Environment Config Schema

This directory contains json schema files for the `mlos_bench` [`Environment`](../../../environments/) [configs](../../environments/).

## Organization

The environment config schema is organized as follows:

- [`environment-schema.json`](./environment-schema.json)

  is the root schema.
  This is the only one that should be referenced in the `"$schema"` field, and only in the top-level.

  This schema references the following subschemas:

  - [`composite-env-subschema.json`](./composite-env-subschema.json)

    This is a subschema that recognizes a `CompositeEnv` environment.

    Since it can include config elements for other leaf elements directly, it also references `leaf-environment-subschema.json`.

  - [`leaf-environment-subschemas.json`](./leaf-environment-subschemas.json)

    This is a simple subschema that simple recognizes one of any of the other concrete `Environment` subschema files, *except* `CompositeEnv`.

    Both leaf and composite environments have common elements, which are defined in the [`base-environment-subschema.json`](./base-environment-subschema.json).

    All other leaf environments are concrete subschemas that extend the base environment subschema.

    For instance:

    - [`local/local-env-subschema.json`](./local/local-env-subschema.json)
    - [`local/local-fileshare-env-subschema.json`](./local/local-fileshare-env-subschema.json)
    - [`remote/os-env-subschema.json`](./remote/os-env-subschema.json)
    - [`remote/remote-env-subschema.json`](./remote/remote-env-subschema.json)
    - [`remote/vm-env-subschema.json`](./remote/vm-env-subschema.json)

    Since nested `"config"` property objects need to specify their own `"unevaluatedProperties": false` setting locally, we also extract common reusable schema elements out to [`common-environment-subschemas.json`.](./common-environment-subschemas.json) for `$ref`-ing.
