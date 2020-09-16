#!/bin/bash
#
# A simple script to generate html docs from Python comments using sphinx.

# Be strict
set -eu

# Be verbose
set -x

# ensure we're in the right folder
scriptdir=$(readlink -f "$(dirname "$0")")
cd "$scriptdir"
MLOS_ROOT=$(readlink -f "$scriptdir/../../")

. "$MLOS_ROOT/scripts/util.sh"
pythonCmd=$(getPythonCmd)

echo "Installing dependencies for generating Python API docs"

$pythonCmd -m pip install -e $MLOS_ROOT/source/Mlos.Python/
$pythonCmd -m pip install sphinx sphinx_rtd_theme numpydoc matplotlib

# Work around some issues with python not picking up the system installed package sometimes.
$pythonCmd -m pip install 'kiwisolver>=1.0.2'

echo "Generating Python API rst files"

sphinx-apidoc -o api -t _templates $MLOS_ROOT/source/Mlos.Python/mlos $MLOS_ROOT/source/Mlos.Python/mlos/unit_tests/* -d 1 -f -e
