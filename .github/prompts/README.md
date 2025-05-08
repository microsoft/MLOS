# Custom `.prompt.md` files for Github Copilot

This directory contains custom `.prompt.md` files for Github Copilot.

These files are used to customize the behavior of Github Copilot when generating code.

The can be invoked with the `/custom-prompt-file-name-prefix` command in the Copilot Chat view (generally when in Agent mode).

For instance:

```txt
/add-sphinx-crossref-to-docstrings
```

will invoke the [`add-sphinx-crossref-to-docstrings.prompt.md`](./add-sphinx-crossref-to-docstrings.prompt.md) file.

Some prompts take additional arguments to help Copilot understand the context of the code being generated or other action to take.

## Types of Custom Prompts

There are two types of custom prompts:

1. Those for MLOS developers (e.g. `add-sphinx-crossref-to-docstrings.prompt.md`).
1. Those for MLOS users (e.g., `generate-mlos-configuration-file.prompt.md`).

## See Also

- <https://code.visualstudio.com/docs/copilot/copilot-customization#_prompt-files-experimental>
- [TODO.md](./TODO.md)
