# MlosCore

This repository contains a stripped down implementation of essentially just the core optimizer and config space description APIs from the original [MLOS](https://github.com/microsoft/MLOS).

It is intended to provide a simplified, easier to consume (e.g. via `pip`), with lower dependencies abstraction to

- describe a space of context, parameters, their ranges, constraints, etc. and result objectives
- an "optimizer" service abstraction (e.g. `register()` and `suggest()`) so we can easily swap out different implementations methods of searching (e.g. random, BO, etc.)

For both design requires intend to reuse as much OSS libraries as possible.

## See Also

[MlosCoreApiDesign.docx](https://microsoft.sharepoint.com/:w:/t/CISLGSL/ESAS3G9q4P5Hoult9uqTfB4B3xh2v6yUfp3YNgIvoyR_IA?e=B6klWZ)
