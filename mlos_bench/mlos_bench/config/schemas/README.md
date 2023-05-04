# Config Schemas

This directory contains [json schemas](https://json-schema.org/) for describing the configuration of the MLOS benchmarking framework.

## Usage

`mlos_bench` `.jsonc` config files can reference these schema files in a couple of ways:

### Internally

If the config file is in the same directory as the schema, it can reference the schema by filename:

```jsonc
{
    "$schema": "../schemas/optimizer-schema.jsonc",
    ...
}
```

### Externally

```jsonc
{
    "$schema": "https://raw.githubusercontent.com/microsoft/MLOS/main/mlos_bench/mlos_bench/config/schemas/optimizer-schema.jsonc",
    ...
}
```

> Note: the above URL is not guaranteed to be stable. It is often recommended to use a specific commit hash or tag in the URL rather than `main` if you depend on that.

## Validation

Within the codebase we use [`jsonschema`](https://pypi.org/project/jsonschema/) to validate config files against the schemas upon loading.

For manual testing, you can use the [`check-jsonschema`](https://pypi.org/project/check-jsonschema/).

For instance:

```shell
check-jsonschema --verbose --default-filetype json5 \
    --schemafile mlos_bench/mlos_bench/config/schemas/optimizers/optimizer-schema.json \
    mlos_bench/mlos_bench/config/optimizers/mlos_core_opt.jsonc
```

## Development

### Conventions

- We do not typically specify `"default"` values in the schema files, since for most validators those aren't enforced, and it would require additional maintenance effort to keep the defaults in sync with the code.
- We typically specify `"additionalProperties": false` in order to prevent typos in the config files from going unnoticed, however this can be overridden for portions of the schema if necessary.

### Editing

Unlike the config files, the schemas are written in plain `json` instead of `jsonc` since some tooling for schema validation doesn't support parsing json files with comments.

When referencing a schema in a config file (see above), the `$schema` property will allow for autocomplete in some editors such as [VSCode](https://code.visualstudio.com/).
