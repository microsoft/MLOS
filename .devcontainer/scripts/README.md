# Devcontainer setup scripts

This directory contains some script variants to preparing the devcontainer environment.

## `.env` file hack

Allow touching (creating but not altering) a `.env` file prior to devcontainer start so those variables can be populated into the devcontainer environment.

See Also: <https://github.com/microsoft/vscode-remote-release/issues/4568>

## `mlos_deps.yml` file hack

When building the devcontainer image, we don't want to include the MLOS source code initially, just its dependencies, so we filter out the MLOS source code from the `mlos.yml` file when building the image and keep the context to that smaller set of files.

When the devcontainer starts, we map the source code (and hence the `mlos.yml` file) into the devcontainer and then run `conda env update` to install the rest of the MLOS dependencies.

This makes the devcontainer base more cacheable.

## Publishing the devcontainer image for cache reuse

The build pipeline publishes the devcontainer image to the Azure Container Registry (ACR) so that it can be reused by other builds.

The secrets for this are stored in the pipeline, but also available in a Key Vault in the MlosCore RG.

One can also use `az acr login` to push an image manually if need be.

### Image cleanup

To save space in the ACR, we purge images older than 7 days.

```sh
#DRY_RUN_ARGS='--dry-run'

PURGE_CMD="acr purge --filter 'devcontainer-cli:.*' --filter 'mlos-devcontainer:.*' --untagged --ago 30d --keep 3 $DRY_RUN_ARGS"

# Setup a daily task:
az acr task create --name dailyPurgeTask --cmd "$PURGE_CMD" --registry mloscore --schedule "0 1 * * *" --context /dev/null

# Or, run it manually.
az acr run --cmd "$PURGE_CMD" --registry mloscore --context /dev/null
```
