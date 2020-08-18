# Uncrustify

This directory contains the uncrustify config used to enforce C++ code style.

We follow something close to the [Google C++ style guidelines](https://google.github.io/styleguide/cppguide.html) with some minor changes to match Microsoft's SqlServer coding style.

We additionally include recent copies of the
[uncrustify binaries for Windows](https://github.com/uncrustify/uncrustify).

Uncrustify can be disabled temporarily by setting the `UncrustifyEnabled=false` property (or via environment variables) for `msbuild`.

Alternatively, one can enable "check only" mode by setting `UncrustifyAutoFix=false`.

See Also:

- `build/Mlos.Cpp.targets`
- `build/Uncrustify.targets`
