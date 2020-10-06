# MLOS Settings System Attributes

This project contains the base classes used by both

- Client code to specify their SettingsRegistry's.
- The SettingsSystem CodeGen tools to evaluate client code provided SettingsRegistry's.

The Attributes directory contains the core C# `Attribute` classes used to help annotate user provided `SettingsRegistry` classes.

Note: there are also non-Settings that are code generated from these attributes such as messages on the shared memory channels.

## See Also

- [MLOS Settings System Code Generation documentation](../Mlos.SettingsSystem.CodeGen/)
