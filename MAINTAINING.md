# Maintaining

Some notes for maintainers.

## Releasing

1. Bump the version using the [`update-version.sh`](./scripts/update-version.sh) script:

    ```sh
    git checkout -b bump-version main
    ./scripts/update-version.sh patch   # or minor or major
    ```

    > This will create a commit and local git tag for that version.
    > You won't be able to create a release from that, so don't push it.

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

6. Update the tag remotely.

    ```sh
    git push --tags
    ```

    > Once this is done, the rules in [`.github/workflows/devcontainer.yml`](./.github/workflows/devcontainer.yml) will automatically publish the wheels to [pypi](https://pypi.org/project/mlos-core/) and tagged docker images to ACR.
    > \
    > Note: This may fail if the version number is already published to pypi, in which case start from the beginning.
