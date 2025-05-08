# Custom Prompt: Add config examples to module docstrings

Let's add config examples to module docstrings in this mlos_bench module.

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

    - Configuration options for these modules should be derived from a JSON, included as a string in the module docstring so users reading the documentation can easily copy/paste, but generally they are loaded from a separate `.mlos.jsonc` config file.

    - The JSON config string should be formatted using `json5` to allow for comments and trailing commas.

    - The JSON config options should conform to the relevant JSON schema for the module, usually defined in the [mlos_bench/configs/schemas](../../mlos_bench/mlos_bench/config/schemas/) directory.
      For instance:

      - For an `mlos_bench.environments` module, the JSON config options should conform to the [mlos_bench/configs/schemas/environments](../../mlos_bench/mlos_bench/config/schemas/environments/environment-schema.json) schema file.
      - For an `mlos_bench.services` module, the JSON config options should conform to the [mlos_bench/configs/schemas/services](../../mlos_bench/mlos_bench/config/schemas/services/service-schema.json) schema file.
      - For an `mlos_bench.schedulers` module, the JSON config options should conform to the [mlos_bench/configs/schemas/schedulers](../../mlos_bench/mlos_bench/config/schemas/schedulers/scheduler-schema.json) schema file.
      - For an `mlos_bench.storage` module, the JSON config options should conform to the [mlos_bench/configs/schemas/storage](../../mlos_bench/mlos_bench/config/schemas/storage/storage-schema.json) schema file.
      - For an `mlos_bench.optimizers` module, the JSON config options should conform to the [mlos_bench/configs/schemas/optimizers](../../mlos_bench/mlos_bench/config/schemas/optimizers/optimizer-schema.json) schema file.

    - The other options that the config can take can often also be found in the parsing of the `config` argument in the `__init__` method body of the class, but they should be included in the module docstring as well.
