# Config Schema Tests

This directory contains tests for the config schemas.

The intention is to provide test cases for

- good examples, both minimal and complete
- bad examples (things that should be rejected by the schema)
- catch places where we have not defined a schema for a new class

To accomplish this, each config schema type has it's own directory containing the following directory layout:

```txt
test_{config_type}_schemas.py
test-cases/
           good/
                partial/
                        test-case-a.jsonc
                        ...
                full/
                        test-case-b.jsonc
                        ...
           bad/
                invalid/
                        test-case-c.jsonc
                        ...
                unhandled/
                        test-case-d.jsonc
                        ...
```

Each `test_{config_type}_schemas.py` file contains a short bit of code that enumerates the test cases in the `test-cases` directory and runs them through the schema validator and checks that the result is as expected according to the directory structure.

There are additionally basic tests to ensure that there appear to be reasonable test coverage for each class implemented in `mlos_bench` and `mlos_core` so that when we add new features they are handled by the schema.

> NOTE: This is by no means a complete check - only a best effort attempt to remind us to take a look at schema test coverage when we add new features.
