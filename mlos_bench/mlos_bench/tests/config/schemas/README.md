# Config Schema Tests

This directory contains tests for the config schemas.

## Goals

The intention is to provide test cases for

- good examples, both minimal and complete
- bad examples (things that should be rejected by the schema)
- catch places where we have not defined a schema for a new class

## Layout

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

Each test case is a jsonc file that contains a single config object.

## Test Code

Each `test_{config_type}_schemas.py` file contains a short bit of code that enumerates the test cases in the `test-cases` directory and runs them through the schema validator and checks that the result is as expected according to the directory structure.

Since there is much boilerplate in that logic repeated across config type, most of that code actually lives in [`__init__.py`](./__init__.py) in this directory.

### Coverage Checks

There are additionally basic tests to ensure that there appear to be reasonable test coverage for each class implemented in `mlos_bench` and `mlos_core` so that when we add new features they are handled by the schema.

> NOTE: This is by no means a complete check - only a best effort attempt to remind us to take a look at schema test coverage when we add new features.

## See Also

- [config/schemas/README.md](../../../config/schemas/README.md)
