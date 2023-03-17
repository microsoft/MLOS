Welcome to MlosCore's documentation!
====================================

.. image:: badges/tests.svg

.. image:: badges/coverage.svg
   :target: htmlcov/index.html

``mlos_core``
-------------

This repository contains a stripped down implementation of essentially just the core optimizer and config space description APIs from the original `MLOS <https://github.com/microsoft/MLOS>`_.

It is intended to provide a simplified, easier to consume (e.g. via ``pip``), with lower dependencies abstraction to

- describe a space of context, parameters, their ranges, constraints, etc. and result objectives
- an "optimizer" service abstraction (e.g. ``register()`` and ``suggest()``) so we can easily swap out different implementations methods of searching (e.g. random, BO, etc.)
- provide some helpers for automating optimization experiment runner loops and data collection

For these design requirements we intend to reuse as much from existing OSS libraries as possible and layer policies and optimizations specifically geared towards autotuning over top.

``mlos_bench``
--------------

This repository also contains the `mlos_bench <./overview.html#mlos-bench-api>`_ module intended to help automate and manage running experiments for autotuning systems with `mlos_core <./overview.html#mlos-core-api>`_.

See Also
--------

- `Source Code <https://aka.ms/mlos-core/src>`_

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

   api/mlos_core/modules
   api/mlos_bench/modules

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Examples

   auto_examples/index
