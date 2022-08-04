Welcome to MlosCore's documentation!
====================================

This repository contains a stripped down implementation of essentially just the core optimizer and config space description APIs from the original `MLOS <https://github.com/microsoft/MLOS>`_ as well as the `mlos-bench` module intended to help automate and manage running experiments for autotuning systems with `mlos-core`.

It is intended to provide a simplified, easier to consume (e.g. via ``pip``), with lower dependencies abstraction to

- describe a space of context, parameters, their ranges, constraints, etc. and result objectives
- an "optimizer" service abstraction (e.g. ``register()`` and ``suggest()``) so we can easily swap out different implementations methods of searching (e.g. random, BO, etc.)
- provide some helpers for automating optimization experiment runner loops and data collection

For these design requirements we intend to reuse as much from existing OSS libraries as possible and layer policies and optimizations specifically geared towards autotuning over top.

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Documentation

   installation
   overview

.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: API Reference

   api/modules

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Examples

   auto_examples/index
