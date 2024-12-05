MLOS Documentation
==================

.. image:: badges/tests.svg

.. image:: badges/coverage.svg
   :target: htmlcov/index.html

`MLOS <source_tree_docs/index.html>`_ is a project to enable `autotuning <autoapi/mlos_core/index.html>`_ with `mlos_core <autoapi/mlos_core/index.html>`_ for systems via `automated benchmarking <autoapi/mlos_bench/index.html>`_ with `mlos_bench </autoapi/mlos_bench/index.html>`_ including managing the storage and `visualization <autoapi/mlos_viz/index.html>`_ of the results via `mlos_viz <autoapi/mlos_viz/index.html>`_.

Documentation is generated from both the `source tree markdown <source_tree_docs/index.html>`_ and the Python docstrings for each of the packages with navigation links on the side.

.. toctree::
   :caption: Source Tree Documentation
   :maxdepth: 4
   :hidden:

   source_tree_docs/index
   source_tree_docs/mlos_core/index
   source_tree_docs/mlos_bench/index
   source_tree_docs/mlos_viz/index

.. toctree::
   :caption: API Reference
   :maxdepth: 2

   autoapi/mlos_core/index
   autoapi/mlos_bench/index
   autoapi/mlos_viz/index

.. toctree::
   :caption: mlos_bench CLI usage
   :maxdepth: 1

   mlos_bench.run.usage

.. toctree::
   :maxdepth: 1
   :caption: References

   Github Source Tree <https://github.com/microsoft/MLOS>
