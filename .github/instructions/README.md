# Custom Copilot Instructions

This directory contains custom instructions for the Copilot AI assistant.
The instructions are designed to guide the AI in providing responses that align with specific project needs and preferences.

## Organization

- Language specific instructions go in their own file, with the cross task instructions in the root of this directory.

    (e.g., [python.instructions.md](python.instructions.md), [bash.instructions.md](bash.instructions.md), [markdown.instructions.md](markdown.instructions.md), [json.instructions.md](json.instructions.md)).

- Instructions relevant to all languages go in the `default.instructions.md` file.

    (e.g., [default.instructions.md](default.instructions.md)).

## See Also

- <https://code.visualstudio.com/docs/copilot/copilot-customization>
- [.vscode/settings.json](../.vscode/settings.json)
  - Configures which of these instructions are used for each file type.
