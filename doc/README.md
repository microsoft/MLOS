# Documentation Generation

Documentation is generated using [`sphinx`](https://www.sphinx-doc.org/).

The configuration for this is in [`doc/source/conf.py`](./source/conf.py).

We use the [`autoapi`](https://sphinx-autoapi.readthedocs.io/en/latest/) extension to generate documentation automatically from the docstrings in our python code.

Additionally, we also use the [`copy-source-tree-docs.sh`](./copy-source-tree-docs.sh) script to copy a few Markdown files from the root of the repository to the `doc/source` build directory automatically to include them in the documentation.

Those are included in the [`index.rst`](./source/index.rst) file which is the main entry point for the documentation and about the only manually maintained rst file.

## Writing Documentation

When writing docstrings, use the [`numpydoc`](https://numpydoc.readthedocs.io/en/latest/format.html) style.

Where necessary embedded [reStructuredText (rst)](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) markup can be used to help format the documentation.

Each top level module should include a docstring that describes the module and its purpose and usage.

These string should be written for consumption by both users and developers.

Other function and method docstrings that aren't typically intended for users can be written for developers.

### Cross Referencing

You can include links between the documentation using [cross-referencing](https://www.sphinx-doc.org/en/master/usage/domains/python.html#python-xref-roles) links in the docstring.

For instance:

```python
"""
My docstring that references another module :py:mod:`fully.qualified.module.name`.

Or else, a class :py:class:`fully.qualified.module.name.ClassName`.

Or else, a class name :py:class:`.ClassName` that is in the same module.

Or else, a class method :py:meth:`~.ClassName.method` but without the leading class name.
"""
```

These links will be automatically resolved by `sphinx` and checked using the `nitpick` option to ensure we have well-formed links in the documentation.

### Example Code

Ideally, each main class should also inclue example code that demonstrates how to use the class.

This code should be included in the docstring and should be runnable via [`doctest`](https://docs.python.org/3/library/doctest.html).

For instance:

```python
class MyClass:
    """
    My class that does something.

    Examples
    --------
    >>> from my_module import MyClass
    >>> my_class = MyClass()
    >>> my_class.do_something()
    Expected output

    """
    ...
```

This code will be automatically checked with `pytest` using the `--doctest-modules` option specified in [`setup.cfg`](../setup.cfg).

## Building the documentation

```sh
# From the root of the repository
make SKIP_COVERAGE=true doc
```

This will also run some checks on the documentation.

> When running this command in a tight loop, it may be useful to run with `SKIP_COVERAGE=true` to avoid re-running the test and coverage checks each time a python file changes.

## Testing

### Manually with Docker

```sh
./nginx-docker.sh restart
```

> Now browse to `http://localhost:8080`

## Troubleshooting

We use the [`intersphinx`](https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html) extension to link between external modules and the [`nitpick`](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-nitpicky) option to ensure that all references resolve correctly.

Unfortunately, this process is not perfect and sometimes we need to provide [`nitpick_ignore`](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-nitpick_ignore)s in the [`doc/source/conf.py`](./source/conf.py) file.

In particular, currently external `TypeVar` and `TypeAliases` are not resolved correctly and we need to ignore those.

In other cases, specifying the full path to the module in the cross-reference or the `import` can help.
