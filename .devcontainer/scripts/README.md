# Devcontainer setup scripts

This directory contains some script variants to preparing the devcontainer environment.

## `.env` file hack

Allow touching (creating but not altering) a `.env` file prior to devcontainer start so those variables can be populated into the devcontainer environment.

See Also: <https://github.com/microsoft/vscode-remote-release/issues/4568>

## `mlos_core_deps.yml` file hack

When building the devcontainer image, we don't want to include the MlosCore source code initially, just its dependencies, so we filter out the MlosCore source code from the `mlos_core.yml` file when building the image and keep the context to that smaller set of files.

When the devcontainer starts, we map the source code (and hence the `mlos_core.yml` file) into the devcontainer and then run `conda env update` to install the rest of the MlosCore dependencies.

This makes the devcontainer base more cacheable.

## Publishing the devcontainer image for cache reuse

The build pipeline publishes the devcontainer image to the Azure Container Registry (ACR) so that it can be reused by other builds.

The secrets for this are stored in the pipeline, but also available in a Key Vault in the MlosCore RG.

One can also use `az acr login` to push an image manually if need be.
