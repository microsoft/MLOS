Installation
============

Development
-----------

0. Create the `mlos_core` Conda environment.

  .. code-block:: shell

    conda env create -f conda-envs/mlos_core.yml

  or

  .. code-block:: shell

    # This will also ensure the environment is update to date using "conda env update -f conda-envs/mlos_core.yml"
    make conda-env


1. Initialize the shell environment.

  .. code-block:: shell

    conda activate mlos_core

2. Run the BayesianOptimization.ipynb notebook.

Distributing
------------

1. Build the *wheel* file.

  .. code-block:: shell

    make dist

2. Install it (e.g. after copying it somewhere else).

  .. code-block:: shell

    # this will install it with emukit support:
    pip install dist/mlos_core-0.0.3-py3-none-any.whl[emukit]

    # this will install it with skopt support:
    pip install dist/mlos_core-0.0.3-py3-none-any.whl[skopt]
