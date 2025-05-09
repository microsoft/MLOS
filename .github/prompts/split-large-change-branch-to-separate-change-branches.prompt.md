# Custom Prompt: Split A Large Change Branch into Separate Change Branches

The branch I have has too many changes and I want to start splitting them out to separate PRs. Can you help me do the following:
1. Run `git diff main > /tmp/git-diff-main.patch` to get the differences between the `main` branch and the current branch and then use `/tmp/git-diff-main.patch` to summarize the changes branch into distinct groups.  You can use the description from the Github PR associated with this branch to see what else was done and needs to be split out.
2. Propose a sequence of changes to stage each of those sets of changes as different self contained and testable PRs.
3. Help me create those PRs by applying that group's changes to new and different branches. We don't need to retain the history of this branch, just the changes.  For instance, we could use `git checkout -b new-branch && git diff -- some/list of/files | git apply -` to make a new branch with some selected changes applied and the use stage only the relevant changes to each file for that particular PR.
Show me the plan and pause to check in with me between each step.
