---
applyTo: "**/*.py"
---

# Python language file instructions

- Include instructions from [default.instructions.md](default.instructions.md) for all languages.
- All functions, methods, classes, and attributes should have docstrings.
- Docstrings should include Sphinx style crossref directives for functions, methods, classes, attributes, and data whenever possible using `:py:class:` or `:py:func:` or `:py:meth:` or `:py:attr:` or `:py:data` syntax, respectively,

  See Also <https://www.sphinx-doc.org/en/master/usage/domains/python.html#python-xref-roles>

- Docstrings for modules should include a summary of the module's purpose and any important details about its usage.
   - Module docstrings should also include an executable example of how to use the module, including any important functions or classes or configuration options (especially those derived from a JSON config file) like any of those in `mlos_bench.environments`, `mlos_bench.services`, `mlos_bench.schedulers`, `mlos_bench.optimizers`, and `mlos_bench.storage`.

      For instance:

        ```python
        '''
        This is an example module docstring for the mlos_bench.environments.my_special_env module.

        It should include some descriptive text about the module and its purpose.

        Example
        -------
        It also includes some executable code examples.

        >>> import json5 as json
        >>> # Load a JSON config string for a MySpecialEnvironment instance.
        >>> json_string = """
        ... {
        ...     "class": "mlos_bench.environments.my_special_env.MySpecialEnvironment",
        ...     "name": "MySpecialEnvironment",
        ...     "config": {
        ...             "param1": 42,
        ...             "param2": "foo",
        ...     },
        ... }
        ... """
        >>> config = json.loads(json_string)

        >>> from mlos_bench.environments.my_special_env import MySpecialEnvironment
        >>> my_env = MySpecialEnvironment(config=config)
        >>> print(my_env)
        MySpecialEnvironment(param1=42, param2='foo')
        '''
        ```

    - Docstrings for classes can refer to their module docstring with `:py:mod:` cross-references for usage examples to allow easier browser navigation of generated documentation.

        For instance:

        ```python
        class MySpecialEnv:
            """
            This is class docstring for MySpecialEnv.

            It should include some descriptive text about the class and its purpose.

            Example
            -------
            Refer to to :py:mod:`mlos_bench.environments.my_special_env` for usage examples.
            """
        ```

- If not all arguments to a function or method fit on the same line, then they should each be on their own line.

    Adding a trailing comma to the last argument is optional, but recommended for consistency whenever a single line is insufficient.

- Code should be formatting using `black`.
- Code should be type checked using `mypy`.
- All function and method parameters should be type annotated.
- Code should be linted using `pylint`.

- Tests should be included for all new code and should be run using `pytest`.
- Tests should be organized roughly the same way as the code they are testing (e.g., `tests/some/test_module.py` for `some/module.py`).
