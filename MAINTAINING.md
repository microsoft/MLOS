# Maintaining

Some notes for maintainers.

## Releasing

1. Bump the version using the [`update-version.sh`](./scripts/update-version.sh) script:

    ```sh
    git checkout -b bump-version main
    ./scripts/update-version.sh --no-tag patch   # or minor or major
    ```

    > By default this would create a local tag, but we would have to overwrite it later, so we skip that step.

2. Test it!

    ```sh
    make dist-test

    # Make sure that the version number on the wheels looks correct.
    ls */dist/*.whl
    ```

3. Make and merge a PR.

4. Update the tag locally.

    Once the PR with the new version files is merged.

    ```sh
    git checkout main
    git pull
    git tag vM.m.p
    ```

    > Note: `M.m.p` is the version number you just bumped to above.

5. Retest!

    ```sh
    make dist-clean
    make dist-test
    ```

6. Update the tag remotely to the MLOS upstream repo.

    ```sh
    git push --tags # upstream (if that's what you called your upstream git remote)
    ```

7. Make a "Release" on Github.

    > Once this is done, the rules in [`.github/workflows/devcontainer.yml`](./.github/workflows/devcontainer.yml) will automatically publish the wheels to [pypi](https://pypi.org/project/mlos-core/) and tagged docker images to ACR.
    > \
    > Note: This may fail if the version number is already published to pypi, in which case start from the beginning with a new patch version.
