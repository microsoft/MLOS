---
applyTo: "**/*.json,**/*.jsonc,**.json5"
---

# JSON language instructions

- Include instructions from [default.instructions.md](default.instructions.md) for all languages.

- Files with a `.json` extension that are ARM templates or JSON schema files should be well formatted and valid JSON, without any comments, trailing commas, etc.
- Files with a `.json` extension that are VSCode settings files (e.g., inside the [.vscode](../../../.vscode)) or [.devcontainer](../../../.devcontainer) directories) should be well formatted and valid JSON, but may contain comments, trailing commas, etc.
- Files with a `.jsonc` or `.json5` extension should be well formatted and valid JSON5 or JSONC or JSON, and can include comments, trailing commas, etc.
- If a file is an `mlos_bench` config, it should have a `.mlos.jsonc` of `.mlos.json` or `.mlos.json5` extension, and should generally match the schemas defined in the [mlos_bench/configs/schemas/](../../../mlos_bench/mlos_bench/config/schemas/) directory (e.g., [mlos-bench-config-schema.json](../../../mlos_bench/mlos_bench/config/schemas/mlos-bench-config-schema.json)), unless it is a test config under the [tests/configs/schemas](../../../mlos_bench/mlos_bench/tests/configs/schemas/) directory.
