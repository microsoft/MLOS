# Service Type Interfaces

Service loading in `mlos_bench` uses a [mix-in](https://en.wikipedia.org/wiki/Mixin#In_Python) approach to combine the functionality of multiple classes specified at runtime through config files into a single class.

This can make type checking in the `Environments` that use those `Services` a little tricky, both for developers and checking tools.

To address this we define `@runtime_checkable` decorated [`Protocols`](https://peps.python.org/pep-0544/) ("interfaces" in other languages) to declare the expected behavior of the `Services` that are loaded at runtime in the `Environments` that use them.
