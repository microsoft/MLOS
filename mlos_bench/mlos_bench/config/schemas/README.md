# Config Schemas

This directory contains [json schemas](https://json-schema.org/) for describing the configuration of the MLOS benchmarking framework.

## Usage

`mlos_bench` `.jsonc` config files can reference these schema files in a couple of ways:

### Implicitly

Certain file extensions are registered with [schemastore.org](https://www.schemastore.org) via their [repository](https://github.com/SchemaStore/schemastore) to allow supporting IDEs to automatically apply schema validation.

```sh
*.mlos.jsonc
*.mlos.json
*.mlos.yaml
*.mlos.yml
```

This makes use of the [`mlos-bench-config-schema.json`](./mlos-bench-config-schema.json) unified schema file in this directory that tries to automatically select the appropriate subschema based on other content within the file.

### Internally

If the config file is in the same directory as the schema (e.g. when editing within this repository), it can reference the schema by filename:

```jsonc
{
    "$schema": "../schemas/optimizer-schema.jsonc",
    ...
}
```

> Note: we usually avoid this approach since it makes it harder to move the schema files around and just doesn't look very nice.
>
> Instead, we try to use on `.vscode/settings.json` to map local repo file globs to their schema files and simply omit the `$schema` field from the config files.

### Externally

```jsonc
{
    "$schema": "https://raw.githubusercontent.com/microsoft/MLOS/main/mlos_bench/mlos_bench/config/schemas/optimizer-schema.jsonc",
    ...
}
```

> Note: the above URL is not guaranteed to be stable. It is often recommended to use a specific commit hash or tag in the URL rather than `main` if you depend on that.

<!-- intentionally blank line to avoid markdown lint complaints -->

> Note: when doing schema development within the `MLOS` repo, this approach may cause false errors to be reported if the remote schema file is different than the local one (and hence config files don't validate quite right).
>
> There is a [deficiency](https://github.com/microsoft/vscode/issues/2809#issuecomment-1544387883) in the `json.schemas` handling in `.vscode/settings.json` that currently prevents remote URLs from being mapping to local files.
>
> A simple workaround for now is to comment out the `$schema` field in the config file while editing, and then uncomment it when you're ready to commit.

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

### Editing

Unlike the config files, the schemas are written in plain `json` instead of `jsonc` since some tooling for schema validation doesn't support parsing json files with comments.
You can add comments within an object using the `"$comment"` property to work around this a little.

When referencing a schema in a config file (see above), the `$schema` property will allow for autocomplete in some editors such as [VSCode](https://code.visualstudio.com/).

### Conventions

- We do not typically specify `"default"` values in the schema files, since for most validators those aren't enforced, and it would require additional maintenance effort to keep the defaults in sync with the code.
- We typically specify `"unevaluatedProperties": false` in order to prevent typos in the config files from going unnoticed, however this can be overridden for portions of the schema if necessary.
  > Note: It's important to use `"unevaluatedProperties": false` from the [2020-09 draft](https://json-schema.org/understanding-json-schema/reference/object.html?highlight=unevaluated#unevaluated-properties), and not `"additionalProperties": false` due to the order in which those two rules get processed.
- When specifying "conditions" always pair the property clause `"properties": { "property-name": { "const": "value" } }` to match it with the `"required": ["property-name"]` clause to ensure that it is a strict match.
- Close all `if-then-else` statements inside a `"oneOf"` block with an `"else": false`, else the clause will implicitly default to `true`.
  > As a nice corollary, this should force a full set of matching descriptions in the `"oneOf"` block so we don't accidentally leave off a supported matching value.
