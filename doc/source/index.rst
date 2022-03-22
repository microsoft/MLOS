Welcome to mlos-core's documentation!
=====================================

This repository contains a stripped down implementation of essentially just the core optimizer and config space description APIs from the original `MLOS <https://github.com/microsoft/MLOS>`_.

It is intended to provide a simplified, easier to consume (e.g. via ``pip``), with lower dependencies abstraction to

- describe a space of context, parameters, their ranges, constraints, etc. and result objectives
- an "optimizer" service abstraction (e.g. ``register()`` and ``suggest()``) so we can easily swap out different implementations methods of searching (e.g. random, BO, etc.)

For both design requires intend to reuse as much OSS libraries as possible.

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Documentation

   installation
   api

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Examples

   auto_examples/index