Installation
============

Development
-----------

The development environment for MLOS uses ``conda`` to ease dependency management.

Devcontainer
------------

For a quick start, you can use the provided `VSCode devcontainer <https://code.visualstudio.com/docs/remote/containers>`_ configuration.

Simply open the project in VSCode and follow the prompts to build and open the devcontainer and the conda environment and additional tools will be installed automatically inside the container.

Manually
--------

  .. note::
    See Also: `conda install instructions <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`_

    Note: to support Windows we rely on some pre-compiled packages from `conda-forge` channels, which increases the `conda` solver time during environment create/update.

    To work around this the (currently) experimental `libmamba` solver can be used.

    See `<https://github.com/conda-incubator/conda-libmamba-solver#getting-started>`_ for more details.


0. Create the `mlos` Conda environment.

  .. code-block:: shell

    conda env create -f conda-envs/mlos.yml


  .. note::
    See the `conda-envs/` directory for additional conda environment files, including those used for Windows (e.g. `conda-envs/mlos-windows.yml`).


  or

  .. code-block:: shell

    # This will also ensure the environment is update to date using "conda env update -f conda-envs/mlos.yml"
    make conda-env


1. Initialize the shell environment.

  .. code-block:: shell

    conda activate mlos

2. Run the BayesianOptimization.ipynb notebook.

Distributing
------------

1. Build the *wheel* file(s).

  .. code-block:: shell

    make dist

2. Install it (e.g. after copying it somewhere else).

  .. code-block:: shell

    # this will install just the optimizer component with emukit support:
    pip install dist/mlos_core-0.1.0-py3-none-any.whl[emukit]

    # this will install just the optimizer component with skopt support:
    pip install dist/mlos_core-0.1.0-py3-none-any.whl[skopt]

  .. code-block:: shell

    # this will install both the optimizer and the experiment runner:
    pip install dist/mlos_bench-0.1.0-py3-none-any.whl

  .. note::

    Note: exact versions may differ due to automatic versioning.
