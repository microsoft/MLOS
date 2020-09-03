# Contributing to MLOS

This project welcomes contributions and suggestions.
Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution.
For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately (e.g., status check, comment).
Simply follow the instructions provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Details

[`main`](https://github.com/microsoft/MLOS/tree/main) is considered the primary development branch.

We expect development to follow a typical "gitflow" style workflow:

1. Fork a copy of the [MLOS repo in Github](https://github.com/microsoft/MLOS).
2. Create a development (a.k.a. topic) branch off of `main` to work on changes.

    ```shell
    git checkout -b YourDevName/some-topic-description main
    ```

3. Submit changes for inclusion as a [Pull Request on Github](https://github.com/microsoft/MLOS/pulls).
4. PRs are associated with [Github Issues](https://github.com/microsoft/MLOS/issues) and need [MLOS-committers](https://github.com/orgs/microsoft/teams/MLOS-committers) to sign-off (in addition to other CI pipeline checks like tests and lint checks to pass).
5. Once approved, the PR can be completed using a squash merge in order to keep a nice linear history.

### Caveats

There are consumers of MLOS internal to Microsoft that use an internal copy of the Github repo targetting code that is not open-sourced.
This arrangement sometimes means porting changes from the internal repo to Github (and vise-versa).
When that happens, the changes are submitted as a PR as described above, with the slight modification of (once approved and passing tests) using a rebase based merge instead of a squash merge in order to allow detecting duplicate patches between the public and private repos.

Additionally, to try and catch breaking changes we run some extra internal integration tests as well.
If they do find issues, we encourage a conversation to occur on how to resolve them in the PRs.
