# Custom Prompt: Add Sphinx Crossref Links to Python Docstrings

Add Sphinx cross-references to python docstrings referencing classes or functions or methods or attributes or data in this file using `:py:class:` or `:py:func:` or `:py:meth:` or `:py:attr:` or `:py:data` syntax, respectively.
\- See Also <https://www.sphinx-doc.org/en/master/usage/domains/python.html#python-xref-roles>

We don't need to do this for the parameter types listed in the Parameters or Returns sections of the docstring though.

For example:

```python
def example_function(param1: MyClass, param2: MyOtherClass) -> SomeOtherType:
    """
    Example function working on an instance of MyClass and MyOtherClass.

    Parameters
    ----------
    param1 : MyClass
        An instance of MyClass.
    param2 : MyOtherClass
        An instance of MyOtherClass.

    Returns
    -------
    SomeOtherType
        An instance of SomeOtherType.
    """
    pass
```

should be changed to:

```python
def example_function(param1: MyClass, param2: MyOtherClass) -> SomeOtherType:
    """
    Example function working on an instance of :py:class:`MyClass` and :py:class:`MyOtherClass`.

    Uses the :py:meth:`MyClass.method_name` method and the :py:attr:`MyOtherClass.attribute_name` attribute.

    Parameters
    ----------
    param1 : MyClass
        An instance of :py:class:`MyClass`.
    param2 : MyOtherClass
        An instance of :py:class:`MyOtherClass`.

    Returns
    -------
    SomeOtherType
        An instance of :py:class:`SomeOtherType`.
    """
    pass
```
