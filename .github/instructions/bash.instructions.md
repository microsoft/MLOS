---
applyTo: "**/*.sh"
---

# Bash shell scripting language instructions

- Include instructions from [default.instructions.md](default.instructions.md) for all languages.

- Scripts schould use `set -e` or `set -o errexit` to exit on error.
- Scripts should use use `set -u` or `set -o nounset` to exit on unset variables.
- Scripts should use `set -o pipefail` to exit on errors in pipelines.
- Commands should be checked for non-zero exit codes and either handled or reported.
- Scripts should use portable syntax for MacOS vs. Linux
- Scripts should validate input.
- Scripts should include usage instructions.
- Scripts should be executable (e.g., `chmod +x`).
- Scripts should include a shebang line (e.g., `#!/usr/bin/env bash`).
- Scripts should be well commented.
- Scripts should include documentation updates if needed.
- Scripts should be well formatted.
- `if` `then` statements should be on the same line.
